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
        field_configs = self.env['panelhex.workcenter.field.config'].search([
            ('workcenter_id', '=', workorder.workcenter_id.id)
        ])

        if field_configs:
            for config in field_configs:
                WorkorderData.create({
                    'workorder_id': workorder.id,
                    'name': config.field_name,
                    'field_type': config.field_type,
                })
        else:
            # No hay configuraciones, usar campos predeterminados del código
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
                default_fields = []

            for field_name, field_type in default_fields:
                WorkorderData.create({
                    'workorder_id': workorder.id,
                    'name': field_name,
                    'field_type': field_type,
                })

class PanelhexWorkorderData(models.Model):
    _name = 'panelhex.workorder.data'
    _description = 'Panelhex Workorder Data'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    workorder_id = fields.Many2one(
        'mrp.workorder', string='Orden de Trabajo', required=True, ondelete='cascade')
    name = fields.Char(string='Nombre del Campo', required=True, tracking=True)
    field_type = fields.Selection([
        ('char', 'Texto'),
        # Otros tipos pueden agregarse si es necesario
    ], string='Tipo de Campo', required=True, tracking=True)
    value = fields.Char(string='Valor', tracking=True)
    field_description = fields.Char(
        string='Descripción del Campo', compute='_compute_field_description', store=True)
    change_history = fields.Text(string='Historial de Cambios', readonly=True)

    @api.depends('name')
    def _compute_field_description(self):
        for record in self:
            record.field_description = record.name.replace('_', ' ').title() if record.name else ''

    def get_value(self):
        self.ensure_one()
        return self.value

    def set_value(self, value):
        self.ensure_one()
        self.value = str(value) if value is not None else ''

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PanelhexWorkorderData, self).create(vals_list)
        for record in records:
            record.add_to_change_history('Creación', record.create_uid.name)
        return records

    def write(self, vals):
        for record in self:
            old_value = record.value
            super(PanelhexWorkorderData, record).write(vals)
            if 'value' in vals:
                new_value = vals['value']
                if old_value != new_value:
                    user = self.env.user.name
                    record.add_to_change_history(
                        'Modificación', user, f"Valor: {old_value} -> {new_value}")
        return True

    def add_to_change_history(self, action_type, user, changes=None):
        self.ensure_one()
        timestamp = fields.Datetime.now()
        new_history = f"{timestamp} - {action_type} por {user}"
        if changes:
            new_history += f": {changes}"
        self.change_history = f"{new_history}\n{self.change_history or ''}"

    @api.constrains('field_type', 'value')
    def _check_value_consistency(self):
        for record in self:
            # Dado que todos los campos son 'char', no es necesario validar otros tipos
            pass
