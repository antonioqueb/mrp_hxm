from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    panelhex_data_ids = fields.One2many('panelhex.workorder.data', 'workorder_id', string='Datos Críticos')

    # Nuevos campos booleanos para las métricas de calidad
    check_tipo_hexagono = fields.Boolean(string="Verificar el tipo de Hexágono")
    check_gramaje = fields.Boolean(string="Check de gramaje")
    check_medidas_bloque = fields.Boolean(string="Validar medidas del bloque gigante")
    check_consistencia_lote = fields.Boolean(string="Check de consistencia del lote")

    check_precision_cortes = fields.Boolean(string="Check de precisión en los cortes")
    check_numero_cortes = fields.Boolean(string="Validar número de cortes correctos por bloque")

    check_alineacion_reticula = fields.Boolean(string="Verificar alineación de la retícula")
    check_calidad_pegado = fields.Boolean(string="Check de calidad del pegado")
    check_resistencia_pegado = fields.Boolean(string="Validar resistencia del pegado")

    check_apariencia_tablero = fields.Boolean(string="Check de apariencia del tablero laminado")
    check_pandeo = fields.Boolean(string="Verificar pandeo")
    check_espesor_medidas = fields.Boolean(string="Validar espesor y medidas")
    check_cantidad_pegamento = fields.Boolean(string="Check de cantidad de pegamento")

    check_acabado_superficial = fields.Boolean(string="Check de acabado superficial")
    check_armado_piezas = fields.Boolean(string="Verificar armado de las piezas")
    check_marcado_etiquetado = fields.Boolean(string="Validar marcado y etiquetado")
    check_seguridad_amarre = fields.Boolean(string="Check de seguridad en el amarre de paquetes")

    # Método para determinar qué campos se deben mostrar según el workcenter_code
    @api.depends('workcenter_id', 'workcenter_id.code')
    def _compute_visible_checks(self):
        for record in self:
            workcenter_code = record.workcenter_id.code if record.workcenter_id else None

            # Inicializar todos los checks como False
            record.update({
                'check_tipo_hexagono': False,
                'check_gramaje': False,
                'check_medidas_bloque': False,
                'check_consistencia_lote': False,
                'check_precision_cortes': False,
                'check_numero_cortes': False,
                'check_alineacion_reticula': False,
                'check_calidad_pegado': False,
                'check_resistencia_pegado': False,
                'check_apariencia_tablero': False,
                'check_pandeo': False,
                'check_espesor_medidas': False,
                'check_cantidad_pegamento': False,
                'check_acabado_superficial': False,
                'check_armado_piezas': False,
                'check_marcado_etiquetado': False,
                'check_seguridad_amarre': False,
            })

            # Activar los checks correspondientes al workcenter_code
            if workcenter_code == 'OCT':
                record.check_tipo_hexagono = True
                record.check_gramaje = True
                record.check_medidas_bloque = True
                record.check_consistencia_lote = True
            elif workcenter_code == 'COR':
                record.check_precision_cortes = True
                record.check_numero_cortes = True
            elif workcenter_code == 'PEG':
                record.check_alineacion_reticula = True
                record.check_calidad_pegado = True
                record.check_resistencia_pegado = True
            elif workcenter_code == 'LAM':
                record.check_apariencia_tablero = True
                record.check_pandeo = True
                record.check_espesor_medidas = True
                record.check_cantidad_pegamento = True
            elif workcenter_code == 'REM':
                record.check_acabado_superficial = True
                record.check_armado_piezas = True
                record.check_marcado_etiquetado = True
                record.check_seguridad_amarre = True

    # Computed field to determine visibility
    visible_checks = fields.Boolean(compute='_compute_visible_checks', store=True)

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
                    ('Lote de Entrada del Rollo', 'char'),
                    ('Peso del Rollo', 'char'),
                    ('Gramaje del Rollo', 'char'),
                    ('Medidas del Rollo', 'char'),
                    ('Número de Corridas', 'char'),
                    ('Tipo de Hexágono de Salida', 'char'),
                ]
            elif workcenter_code == 'COR':
                default_fields = [
                    ('Número de Cortes por turno', 'char'),
                    ('Número de Cortes de cada bloque', 'char')
                ]
            elif workcenter_code == 'PEG':
                default_fields = [
                    ('Retículas pegadas por turno', 'char'),
                ]
            elif workcenter_code == 'LAM':
                default_fields = [
                    ('Lote de Retícula de Entrada', 'char'),
                    ('Lote de Rollo Superior de Entrada', 'char'),
                    ('Lote de Rollo Inferior de Entrada', 'char'),
                    ('Cantidad de Metros Lineales por turno', 'char'),
                    ('Especificación del material laminado', 'char'),
                    ('Código de producto', 'char'),
                    ('Merma generada', 'char'),
                    ('Kilogramos de Pegamento utilizado', 'char'),
                ]
            elif workcenter_code == 'REM':
                default_fields = [
                    ('Número de Tarimas de PT por turno', 'char'),
                    ('Especificación del material laminado', 'char'),
                    ('Código de producto', 'char'),
                    ('Número de tarimas producidas de la Orden de producción', 'char'),
                    ('Merma Generada', 'char')
                ]
            else:
                default_fields = []

            for field_name, field_type in default_fields:
                WorkorderData.create({
                    'workorder_id': workorder.id,
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
