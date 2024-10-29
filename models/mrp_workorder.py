from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    panelhex_data_ids = fields.One2many('panelhex.workorder.data', 'workorder_id', string='Datos Hexamex')

    @api.model
    def create(self, vals):
        res = super(MrpWorkorder, self).create(vals)
        if res.workcenter_id:
            self.create_default_workorder_data(res)
        return res

    def create_default_workorder_data(self, workorder):
        WorkorderData = self.env['panelhex.workorder.data']
        workcenter_code = workorder.workcenter_id.code
        if workcenter_code == 'OCT':
            default_fields = [
                ('entrada_rollo_lote', 'char'),
                ('entrada_rollo_proveedor', 'char'),
                ('entrada_rollo_peso', 'char'),
                ('entrada_rollo_gramaje', 'char'),
                ('entrada_rollo_medidas', 'char'),
                ('salida_num_corridas', 'char'),
                ('salida_tipo_hexagono', 'char'),
                ('operador', 'char'),
            ]
        elif workcenter_code == 'COR':
            default_fields = [
                ('entrada_lote_bloque', 'char'),
                ('salida_num_cortes', 'char'),
                ('operador', 'char'),
            ]
        elif workcenter_code == 'PEG':
            default_fields = [
                ('salida_num_reticulas', 'char'),
                ('salida_lote_tarima', 'char'),
                ('fecha_pegado', 'date'),
            ]
        elif workcenter_code == 'LAM':
            default_fields = [
                ('entrada_reticula_lote', 'char'),
                ('entrada_rollo_superior_lote', 'char'),
                ('entrada_rollo_inferior_lote', 'char'),
                ('salida_metros_lineales', 'char'),
                ('salida_especificacion', 'char'),
                ('cliente', 'char'),
                ('codigo_producto', 'char'),
                ('merma_generada', 'char'),
                ('kg_pegamento_utilizado', 'char'),
                ('operador', 'char'),
            ]
        elif workcenter_code == 'REM':
            default_fields = [
                ('entrada_tablero_lote', 'char'),
                ('salida_num_tarimas', 'char'),
                ('salida_especificacion', 'char'),
                ('cliente', 'char'),
                ('codigo_producto', 'char'),
                ('merma_generada', 'char'),
                ('operador', 'char'),
            ]
        else:
            default_fields = []  # Default empty list for unknown workcenter codes..

        for field, field_type in default_fields:
            WorkorderData.create({
                'workorder_id': workorder.id,
                'name': field,
                'field_type': field_type,
            })

class PanelhexWorkorderData(models.Model):
    _name = 'panelhex.workorder.data'
    _description = 'Panelhex Workorder Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True, ondelete='cascade')
    name = fields.Char(string='Field Name', required=True, tracking=True)
    field_type = fields.Selection([
        ('char', 'Text'),
        ('float', 'Number'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('many2one', 'Relation'),
    ], string='Field Type', required=True, tracking=True)
    value_char = fields.Char(string='Text Value', tracking=True)
    value_float = fields.Float(string='Number Value', tracking=True)
    value_integer = fields.Integer(string='Integer Value', tracking=True)
    value_boolean = fields.Boolean(string='Boolean Value', tracking=True)
    value_many2one = fields.Many2one('res.partner', string='Relation Value', tracking=True)
    value_date = fields.Date(string='Date Value', tracking=True)
    field_description = fields.Char(string='Field Description', compute='_compute_field_description', store=True)
    change_history = fields.Char(string='Historial de Cambios', readonly=True)

    @api.depends('name')
    def _compute_field_description(self):
        for record in self:
            if record.name:
                record.field_description = record.name.replace('_', ' ').title()
            else:
                record.field_description = ''

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PanelhexWorkorderData, self).create(vals_list)
        for record in records:
            record.add_to_change_history('Creación', record.create_uid.name)
        return records

    def write(self, vals):
        for record in self:
            changes = []
            for field, value in vals.items():
                if field in self._fields and getattr(self._fields[field], 'tracking', False):
                    old_value = record[field]
                    if old_value != value:
                        changes.append(f"{field}: {old_value} -> {value}")
            
            if changes:
                user = self.env.user.name
                change_description = ", ".join(changes)
                record.add_to_change_history('Modificación', user, change_description)

        return super(PanelhexWorkorderData, self).write(vals)

    def add_to_change_history(self, action_type, user, changes=None):
        self.ensure_one()
        timestamp = fields.Datetime.now()
        new_history = f"{timestamp} - {action_type} por {user}"
        if changes:
            new_history += f": {changes}"
        
        if self.change_history:
            self.change_history = f"{new_history}\n{self.change_history}"[:255]  # Limitamos a 255 caracteres
        else:
            self.change_history = new_history[:255]  # Limitamos a 255 caracteres

    def get_formview_id(self, access_uid=None):
        """ Devuelve el contexto actualizado con el tipo de campo actual """
        res = super(PanelhexWorkorderData, self).get_formview_id(access_uid)
        return {
            'id': res,
            'context': {'current_field_type': self.field_type},
        }

    @api.onchange('field_type')
    def _onchange_field_type(self):
        # Clear all value fields when field_type changes
        self.value_char = False
        self.value_float = False
        self.value_integer = False
        self.value_boolean = False
        self.value_many2one = False
        self.value_date = False

    @api.constrains('field_type', 'value_char', 'value_float', 'value_integer', 'value_boolean', 'value_many2one', 'value_date')
    def _check_value_consistency(self):
        for record in self:
            if record.field_type == 'char' and record.value_char:
                continue
            elif record.field_type == 'float' and record.value_float is not False:
                continue
            elif record.field_type == 'integer' and record.value_integer is not False:
                continue
            elif record.field_type == 'boolean' and record.value_boolean is not None:
                continue
            elif record.field_type == 'many2one' and record.value_many2one:
                continue
            elif record.field_type == 'date' and record.value_date:
                continue
            elif not any([record.value_char, record.value_float, record.value_integer, record.value_boolean, record.value_many2one, record.value_date]):
                # Allow empty values during creation
                continue
            else:
                raise ValidationError(f"Please provide a value for the field '{record.name}' of type '{record.field_type}'")

    def get_value(self):
        self.ensure_one()
        if self.field_type == 'char':
            return self.value_char
        elif self.field_type == 'float':
            return self.value_float
        elif self.field_type == 'integer':
            return self.value_integer
        elif self.field_type == 'boolean':
            return self.value_boolean
        elif self.field_type == 'many2one':
            return self.value_many2one.id if self.value_many2one else False
        elif self.field_type == 'date':
            return self.value_date
        return False

    def set_value(self, value):
        self.ensure_one()
        if self.field_type == 'char':
            self.value_char = value
        elif self.field_type == 'float':
            self.value_float = float(value) if value else False
        elif self.field_type == 'integer':
            self.value_integer = int(value) if value else False
        elif self.field_type == 'boolean':
            self.value_boolean = bool(value)
        elif self.field_type == 'many2one':
            self.value_many2one = self.env['res.partner'].browse(int(value)) if value else False
        elif self.field_type == 'date':
            self.value_date = value