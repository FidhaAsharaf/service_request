from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class ServiceRequest(models.Model):
    _name = 'service.request'
    _description = 'Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'

    reference = fields.Char(string="Reference", default=lambda self: _('New'), readonly=True, copy=False,
                            help="Reference Number for service request")
    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    request_date = fields.Date(string="Request Date", default=fields.Date.today)
    description = fields.Text(string="Description", required=True)
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Priority",
                                default='low')
    estimated_cost = fields.Float(string="Estimated Cost")
    state = fields.Selection(
        [('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Status", default='draft', tracking=True)
    assigned_user_id = fields.Many2one('res.users', string="Assigned User")
    related_task_id = fields.Many2one('project.task', string="Related Task", readonly=True)
    approval_reason = fields.Text(string="Approval Reason")
    active = fields.Boolean(string="Active", default=True)
    task_count = fields.Integer(
        string="Task Count",
        compute="_compute_task_count"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            """Automatically generate a reference number for service request."""
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('service.request')
            return super(ServiceRequest, self).create(vals)

    def action_submit(self):

        for rec in self:

            if not rec.estimated_cost:
                raise ValidationError(
                    _("Please add estimated cost before submission.")
                )

            rec.state = 'submitted'

            rec.message_post(
                body="Service Request submitted."
            )

    def action_approve(self):
        limit = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'service_request_management.approval_cost_limit',
                default=5000
            )
        )
        for rec in self:

            if (
                    rec.estimated_cost > limit
                    and not self.env.user.has_group(
                'service_request_management.group_service_request_manager'
            )
            ):
                raise ValidationError(
                    _("Approval above limit 5000 is restricted to managers.")
                )

            rec.state = 'approved'

            rec.message_post(
                body="Service Request approved."
            )

    def action_reject(self):

        for rec in self:
            rec.state = 'rejected'

            rec.message_post(
                body="Service Request rejected."
            )



    def unlink(self):

        for rec in self:

            if rec.state == 'approved':
                raise ValidationError(
                    _("Approved requests cannot be deleted.")
                )

        return super().unlink()

    def write(self, vals):

        for rec in self:

            if (
                    rec.state != 'draft'
                    and self.env.user.has_group(
                'service_request_management.group_service_request_employee'
            )
                    and not self.env.user.has_group(
                'service_request_management.group_service_request_manager'
            )
            ):

                allowed_fields = ['state','related_task_id',]

                edited_fields = list(vals.keys())

                for field in edited_fields:

                    if field not in allowed_fields:
                        raise ValidationError(
                            _("Only draft requests can be edited.")
                        )

        return super().write(vals)

    def _compute_task_count(self):

        for rec in self:
            rec.task_count = self.env['project.task'].search_count([
                ('id', '=', rec.related_task_id.id)
            ])

    def action_create_project_task(self):

        for rec in self:

            if rec.related_task_id:
                raise ValidationError(
                    _("Project Task already created.")
                )

            task = self.env['project.task'].create({
                'name': rec.reference,
                'description': rec.description,
            })

            rec.related_task_id = task.id

            rec.message_post(
                body="Project Task created successfully."
            )

    def action_view_project_task(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Task',
            'res_model': 'project.task',
            'view_mode': 'form',
            'res_id': self.related_task_id.id,
            'target': 'current',
        }

    def action_pending_approval_reminder(self):

        pending_requests = self.search([
            ('state', '=', 'submitted'),
            ('request_date', '<=', fields.Datetime.now() - timedelta(days=3))
        ])

        template = self.env.ref(
            'service_request_management.email_template_service_request_reminder'
        )

        manager_group = self.env.ref(
            'service_request_management.group_service_request_manager'
        )

        manager_emails = manager_group.users.mapped('email')

        email_to = ','.join(manager_emails)

        for rec in pending_requests:

            if email_to:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={
                        'email_to': email_to
                    }
                )

                rec.message_post(
                    body="Reminder email sent to managers for pending approval."
                )
