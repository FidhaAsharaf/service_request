# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    approval_cost_limit = fields.Integer(
        string="Approval Cost Limit",
        config_parameter='service_request_management.approval_cost_limit',
        help="Requests above this amount can only be approved by managers."
    )


