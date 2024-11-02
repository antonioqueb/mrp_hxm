from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class ProgramaMaestroProduccion(models.Model):
    _name = 'panelhex.programa.maestro.produccion'
    _description = 'Programa Maestro de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc'

    # Campos del modelo
    name = fields.Char(string='Nombre', required=True, copy=False, tracking=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True, tracking=True)
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True, tracking=True)
    fecha_fin = fields.Date(string='Fecha de Fin', required=True, tracking=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('planificado', 'Planificado'),
        ('en_proceso', 'En Proceso'),
        ('terminado', 'Terminado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='borrador', tracking=True)
    safety_stock = fields.Float(string='Stock de Seguridad', tracking=True, default=0.0)
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_demand_forecast')
    critical_stock = fields.Float(string='Stock Crítico', tracking=True, default=0.0)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_suggested_replenishment')
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_forecasted_stock')
    monthly_data = fields.One2many('panelhex.programa.maestro.produccion.mensual', 'plan_id', string='Datos Mensuales')
    notas = fields.Text(string='Notas')
    qty_available = fields.Float(string='Stock a Mano', compute='_compute_stock_fields')
    daily_average_consumption = fields.Float(string='Consumo Promedio Diario', compute='_compute_daily_average_consumption')
    coverage_days = fields.Float(string='Días de Cobertura', compute='_compute_coverage_days')
    demand_stock_difference = fields.Float(string='Demanda Pronosticada - Stock Previsto', compute='_compute_demand_stock_difference')

    # Función de ayuda para calcular meses
    def _calculate_total_months(self, start_date, end_date):
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1

    @api.depends('demand_forecast', 'forecasted_stock')
    def _compute_demand_stock_difference(self):
        for record in self:
            record.demand_stock_difference = record.demand_forecast - record.forecasted_stock

    @api.depends('qty_available', 'daily_average_consumption')
    def _compute_coverage_days(self):
        for record in self:
            record.coverage_days = record.qty_available / record.daily_average_consumption if record.daily_average_consumption > 0 else 0.0

    @api.depends('demand_forecast', 'fecha_inicio', 'fecha_fin')
    def _compute_daily_average_consumption(self):
        for record in self:
            total_days = (record.fecha_fin - record.fecha_inicio).days + 1 if record.fecha_inicio and record.fecha_fin else 0
            record.daily_average_consumption = record.demand_forecast / total_days if total_days > 0 else 0.0

    @api.depends('product_id')
    def _compute_stock_fields(self):
        for record in self:
            record.qty_available = record.product_id.with_context(company_id=self.env.company.id, location_id=False).qty_available if record.product_id else 0.0

    @api.depends('monthly_data.demand_forecast')
    def _compute_demand_forecast(self):
        for record in self:
            record.demand_forecast = sum(record.monthly_data.mapped('demand_forecast'))

    @api.depends('monthly_data.suggested_replenishment')
    def _compute_suggested_replenishment(self):
        for record in self:
            record.suggested_replenishment = sum(record.monthly_data.mapped('suggested_replenishment'))

    @api.depends('monthly_data.forecasted_stock')
    def _compute_forecasted_stock(self):
        for record in self:
            record.forecasted_stock = sum(record.monthly_data.mapped('forecasted_stock'))

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_dates(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin and record.fecha_inicio > record.fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")

    # Métodos de acción y lógica adicional
    def action_confirmar(self):
        self._set_estado('borrador', 'confirmado')

    def action_iniciar(self):
        self._set_estado('planificado', 'en_proceso')

    def action_terminar(self):
        self._set_estado('en_proceso', 'terminado')

    def action_cancelar(self):
        for record in self:
            if record.estado in ['terminado', 'cancelado']:
                raise UserError("No se pueden cancelar programas terminados o ya cancelados.")
            record.write({'estado': 'cancelado'})

    def action_borrador(self):
        self._set_estado('cancelado', 'borrador')

    # Método de ayuda para cambiar el estado
    def _set_estado(self, estado_actual, nuevo_estado):
        for record in self:
            if record.estado != estado_actual:
                raise UserError(f"Solo se pueden modificar programas en estado {estado_actual}.")
            record.write({'estado': nuevo_estado})

    @api.model
    def create(self, vals):
        programa = super().create(vals)
        programa._create_monthly_data()
        return programa

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ['fecha_inicio', 'fecha_fin', 'product_id', 'safety_stock']):
            self._create_monthly_data()
        return res

    def _create_monthly_data(self):
        self.ensure_one()
        if not self.product_id:
            _logger.warning("No se puede crear datos mensuales sin un producto seleccionado.")
            return

        self.monthly_data.unlink()
        current_date = self.fecha_inicio
        while current_date <= self.fecha_fin:
            next_month = current_date + relativedelta(months=1)
            self.env['panelhex.programa.maestro.produccion.mensual'].create({
                'plan_id': self.id,
                'date': current_date,
                'product_id': self.product_id.id,
            })
            current_date = next_month

    def action_generate_production_orders(self):
        self.ensure_one()
        if self.estado != 'confirmado':
            raise UserError("Solo se pueden generar órdenes de producción para programas confirmados.")

        for monthly_data in self.monthly_data:
            if monthly_data.suggested_replenishment > 0:
                existing_mo = self.env['mrp.production'].search([
                    ('product_id', '=', self.product_id.id),
                    ('date_deadline', '=', monthly_data.date),
                    ('origin', '=', f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}")
                ])
                if not existing_mo:
                    self.env['mrp.production'].create({
                        'product_id': self.product_id.id,
                        'product_qty': monthly_data.suggested_replenishment,
                        'date_deadline': monthly_data.date,
                        'origin': f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}",
                    })

        self.write({'estado': 'planificado'})
