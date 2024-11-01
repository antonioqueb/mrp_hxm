# models/panelhex_workcenter_field_config.py
from odoo import models, fields

class WorkcenterFieldConfig(models.Model):
    _name = 'panelhex.workcenter.field.config'
    _description = 'Configuración de Campos por Centro de Trabajo'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Centro de Trabajo', required=True)
    field_name = fields.Char(string='Nombre del Campo', required=True)
    field_type = fields.Selection([
        ('char', 'Texto'),
        ('float', 'Número'),
        ('integer', 'Entero'),
        ('boolean', 'Booleano'),
        ('many2one', 'Relación'),
    ], string='Tipo de Campo', required=True)
