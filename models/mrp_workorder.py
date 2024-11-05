from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    code = fields.Char(related='workcenter_id.code', string='Código del Centro de Trabajo', store=True)


    panelhex_data_ids = fields.One2many('panelhex.workorder.data', 'workorder_id', string='Datos Críticos')

    # Campos booleanos para las métricas de calidad
    # Campos booleanos para las métricas de calidad
    check_tipo_hexagono = fields.Boolean(string="Verificar el tipo de Hexágono", default=False)
    check_gramaje = fields.Boolean(string="Check de gramaje", default=False)
    check_medidas_bloque = fields.Boolean(string="Validar medidas del bloque gigante", default=False)
    check_consistencia_lote = fields.Boolean(string="Check de consistencia del lote", default=False)
    check_precision_cortes = fields.Boolean(string="Check de precisión en los cortes", default=False)
    check_numero_cortes = fields.Boolean(string="Validar número de cortes correctos por bloque", default=False)
    check_alineacion_reticula = fields.Boolean(string="Verificar alineación de la retícula", default=False)
    check_calidad_pegado = fields.Boolean(string="Check de calidad del pegado", default=False)
    check_resistencia_pegado = fields.Boolean(string="Validar resistencia del pegado", default=False)
    check_apariencia_tablero = fields.Boolean(string="Check de apariencia del tablero laminado", default=False)
    check_pandeo = fields.Boolean(string="Verificar pandeo", default=False)
    check_espesor_medidas = fields.Boolean(string="Validar espesor y medidas", default=False)
    check_cantidad_pegamento = fields.Boolean(string="Check de cantidad de pegamento", default=False)
    check_acabado_superficial = fields.Boolean(string="Check de acabado superficial", default=False)
    check_armado_piezas = fields.Boolean(string="Verificar armado de las piezas", default=False)
    check_marcado_etiquetado = fields.Boolean(string="Validar marcado y etiquetado", default=False)
    check_seguridad_amarre = fields.Boolean(string="Check de seguridad en el amarre de paquetes", default=False)


   

    visible_checks = fields.Boolean(compute='_compute_visible_checks', store=True)

    @api.model
    def create(self, vals):
        res = super(MrpWorkorder, self).create(vals)
        if res.workcenter_id:
            res.create_default_workorder_data()
        return res

    def create_default_workorder_data(self):
        WorkorderData = self.env['panelhex.workorder.data']
        field_configs = self.env['panelhex.workcenter.field.config'].search([
            ('workcenter_id', '=', self.workcenter_id.id)
        ])

        default_fields_mapping = {
            'OCT': [
                ('Lote de Entrada del Rollo', 'char'),
                ('Peso del Rollo', 'char'),
                ('Gramaje del Rollo', 'char'),
                ('Medidas del Rollo', 'char'),
                ('Número de Corridas', 'char'),
                ('Tipo de Hexágono de Salida', 'char')
            ],
            'COR': [
                ('Número de Cortes por turno', 'char'),
                ('Número de Cortes de cada bloque', 'char')
            ],
            'PEG': [
                ('Retículas pegadas por turno', 'char')
            ],
            'LAM': [
                ('Lote de Retícula de Entrada', 'char'),
                ('Lote de Rollo Superior de Entrada', 'char'),
                ('Lote de Rollo Inferior de Entrada', 'char'),
                ('Cantidad de Metros Lineales por turno', 'char'),
                ('Especificación del material laminado', 'char'),
                ('Código de producto', 'char'),
                ('Merma generada', 'char'),
                ('Kilogramos de Pegamento utilizado', 'char')
            ],
            'REM': [
                ('Número de Tarimas de PT por turno', 'char'),
                ('Especificación del material laminado', 'char'),
                ('Código de producto', 'char'),
                ('Número de tarimas producidas de la Orden de producción', 'char'),
                ('Merma Generada', 'char')
            ]
        }

        if field_configs:
            for config in field_configs:
                WorkorderData.create({
                    'workorder_id': self.id,
                    'name': config.field_name,
                    'field_type': config.field_type,
                })
        else:
            workcenter_code = self.workcenter_id.code
            default_fields = default_fields_mapping.get(workcenter_code, [])
            for field_name, field_type in default_fields:
                WorkorderData.create({
                    'workorder_id': self.id,
                    'name': field_name,
                    'field_type': field_type,
                })

    @api.model
    def _get_workcenters_for_user(self):
        user_employee = self.env.user.employee_id
        if user_employee:
            return self.env['mrp.workcenter'].search([
                ('allowed_employee_ids', 'in', [user_employee.id])
            ])
        return self.env['mrp.workcenter'].search([])

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
            record.field_description = record.name if record.name else ''

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
        # Dado que todos los campos son 'char', no es necesario validar otros tipos
        pass
