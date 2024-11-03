# models/mrp_workcenter.py
from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipo_id = fields.Many2one('panelhex.equipo', string='Equipo Hexamex')
    allowed_employee_ids = fields.Many2many(
        'hr.employee',
        string='Empleados Autorizados',
        help='Lista de empleados que pueden acceder a este centro de trabajo'
    )
