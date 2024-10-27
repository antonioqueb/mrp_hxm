from odoo import models, fields, api

class PanelhexWorkorderData(models.Model):
    _name = 'panelhex.workorder.data'
    _description = 'Datos Específicos de Orden de Trabajo'

    workorder_id = fields.Many2one('mrp.workorder', string="Orden de Trabajo", required=True)
    name = fields.Char(string="Nombre del Campo", required=True)
    field_type = fields.Selection([
        ('char', 'Texto'),
        ('boolean', 'Booleano'),
        ('integer', 'Número Entero')
    ], string="Tipo de Campo", required=True)
    value_char = fields.Char(string="Valor Texto")
    value_boolean = fields.Boolean(string="Valor Booleano")
    value_integer = fields.Integer(string="Valor Entero")

    @api.depends('name')
    def _compute_field_description(self):
        for record in self:
            if record.name:
                record.field_description = record.name.replace('_', ' ').title()
            else:
                record.field_description = ''

    field_description = fields.Char(string="Descripción del Campo", compute='_compute_field_description', store=True)

    @api.depends('field_type', 'value_char', 'value_boolean', 'value_integer')
    def _compute_value(self):
        for record in self:
            if record.field_type == 'char':
                record.value = record.value_char
            elif record.field_type == 'boolean':
                record.value = str(record.value_boolean)
            elif record.field_type == 'integer':
                record.value = str(record.value_integer)

    value = fields.Char(string="Valor", compute='_compute_value', store=True)

    @api.onchange('field_type')
    def _onchange_field_type(self):
        if self.field_type == 'char':
            self.value_boolean = False
            self.value_integer = 0
        elif self.field_type == 'boolean':
            self.value_char = ''
            self.value_integer = 0
        elif self.field_type == 'integer':
            self.value_char = ''
            self.value_boolean = False

    def get_value(self):
        self.ensure_one()
        if self.field_type == 'char':
            return self.value_char
        elif self.field_type == 'boolean':
            return self.value_boolean
        elif self.field_type == 'integer':
            return self.value_integer

    def set_value(self, val):
        self.ensure_one()
        if self.field_type == 'char':
            self.value_char = val
        elif self.field_type == 'boolean':
            self.value_boolean = bool(val)
        elif self.field_type == 'integer':
            self.value_integer = int(val)