from odoo import models, fields, api

class HexamexWorkorderData(models.Model):
    _name = 'Hexamex.workorder.data'
    _description = 'Datos Específicos de Orden de Trabajo'

    workorder_id = fields.Many2one('mrp.workorder', string="Orden de Trabajo", required=True)
    name = fields.Char(string="Nombre del Campo", required=True)
    field_type = fields.Selection([
        ('char', 'Texto'),
        ('float', 'Número Decimal'),
        ('integer', 'Número Entero'),
        ('selection', 'Selección'),
        ('many2one', 'Relación'),
        ('json', 'JSON')
    ], string="Tipo de Campo", required=True)
    value_char = fields.Char(string="Valor (Texto)")
    value_float = fields.Float(string="Valor (Decimal)")
    value_integer = fields.Integer(string="Valor (Entero)")
    value_selection = fields.Char(string="Valor (Selección)")
    value_many2one = fields.Integer(string="Valor (Relación)")
    value_json = fields.Json(string="Valor (JSON)")

    @api.depends('name', 'field_type')
    def _compute_field_description(self):
        for record in self:
            if record.name:
                record.field_description = record.name.replace('_', ' ').title()
            else:
                record.field_description = ''

    field_description = fields.Char(string="Descripción del Campo", compute='_compute_field_description', store=True)