from odoo import models, fields, api
import json

class PanelhexWorkorderData(models.Model):
    _name = 'panelhex.workorder.data'
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
    value = fields.Char(string="Valor")

    @api.depends('name', 'field_type')
    def _compute_field_description(self):
        for record in self:
            if record.name:
                record.field_description = record.name.replace('_', ' ').title()
            else:
                record.field_description = ''

    field_description = fields.Char(string="Descripción del Campo", compute='_compute_field_description', store=True)

    def get_value(self):
        self.ensure_one()
        if self.field_type == 'float':
            return float(self.value) if self.value else 0.0
        elif self.field_type == 'integer':
            return int(self.value) if self.value else 0
        elif self.field_type == 'many2one':
            return int(self.value) if self.value else False
        elif self.field_type == 'json':
            return json.loads(self.value) if self.value else {}
        else:  # char, selection
            return self.value

    def set_value(self, val):
        self.ensure_one()
        if self.field_type == 'float':
            self.value = str(float(val))
        elif self.field_type == 'integer':
            self.value = str(int(val))
        elif self.field_type == 'many2one':
            self.value = str(int(val)) if val else False
        elif self.field_type == 'json':
            self.value = json.dumps(val)
        else:  # char, selection
            self.value = str(val)

    @api.model
    def create(self, vals):
        if 'value' in vals and 'field_type' in vals:
            temp = self.new(vals)
            temp.set_value(vals['value'])
            vals['value'] = temp.value
        return super(PanelhexWorkorderData, self).create(vals)

    def write(self, vals):
        if 'value' in vals:
            for record in self:
                temp_value = vals['value']
                record.set_value(temp_value)
                vals['value'] = record.value
        return super(PanelhexWorkorderData, self).write(vals)