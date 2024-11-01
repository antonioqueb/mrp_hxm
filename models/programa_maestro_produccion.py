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
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_demand_forecast', store=True)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_suggested_replenishment', store=True)
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_forecasted_stock', store=True)
    monthly_data = fields.One2many('panelhex.programa.maestro.produccion.mensual', 'plan_id', string='Datos Mensuales')
    notas = fields.Text(string='Notas')

    @api.depends('monthly_data.demand_forecast')
    def _compute_demand_forecast(self):
        for record in self:
            try:
                record.demand_forecast = sum(record.monthly_data.mapped('demand_forecast'))
            except Exception as e:
                _logger.error(f"Error al calcular la demanda pronosticada: {str(e)}")
                record.demand_forecast = 0.0

    @api.depends('monthly_data.suggested_replenishment')
    def _compute_suggested_replenishment(self):
        for record in self:
            try:
                record.suggested_replenishment = sum(record.monthly_data.mapped('suggested_replenishment'))
            except Exception as e:
                _logger.error(f"Error al calcular el reabastecimiento sugerido: {str(e)}")
                record.suggested_replenishment = 0.0

    @api.depends('monthly_data.forecasted_stock')
    def _compute_forecasted_stock(self):
        for record in self:
            try:
                record.forecasted_stock = sum(record.monthly_data.mapped('forecasted_stock'))
            except Exception as e:
                _logger.error(f"Error al calcular el stock previsto: {str(e)}")
                record.forecasted_stock = 0.0

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_dates(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin and record.fecha_inicio > record.fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")

    def action_confirmar(self):
        for record in self:
            if record.estado != 'borrador':
                raise UserError("Solo se pueden confirmar programas en estado borrador.")
            record.write({'estado': 'confirmado'})

    def action_iniciar(self):
        for record in self:
            if record.estado != 'planificado':
                raise UserError("Solo se pueden iniciar programas en estado planificado.")
            record.write({'estado': 'en_proceso'})

    def action_terminar(self):
        for record in self:
            if record.estado != 'en_proceso':
                raise UserError("Solo se pueden terminar programas en proceso.")
            record.write({'estado': 'terminado'})

    def action_cancelar(self):
        for record in self:
            if record.estado in ['terminado', 'cancelado']:
                raise UserError("No se pueden cancelar programas terminados o ya cancelados.")
            record.write({'estado': 'cancelado'})

    def action_borrador(self):
        for record in self:
            if record.estado != 'cancelado':
                raise UserError("Solo se pueden volver a borrador los programas cancelados.")
            record.write({'estado': 'borrador'})

    @api.model
    def create(self, vals):
        programa = super(ProgramaMaestroProduccion, self).create(vals)
        try:
            programa._create_monthly_data()
        except Exception as e:
            _logger.error(f"Error al crear los datos mensuales: {str(e)}")
        return programa

    def write(self, vals):
        res = super(ProgramaMaestroProduccion, self).write(vals)
        try:
            if any(key in vals for key in ['fecha_inicio', 'fecha_fin', 'product_id', 'safety_stock']):
                self._create_monthly_data()
        except Exception as e:
            _logger.error(f"Error al actualizar los datos mensuales: {str(e)}")
        return res

    def _create_monthly_data(self):
        self.ensure_one()
        try:
            if not self.product_id:
                _logger.warning("No se puede crear datos mensuales sin un producto seleccionado.")
                return

            self.monthly_data.unlink()
            current_date = self.fecha_inicio
            while current_date <= self.fecha_fin:
                next_month = current_date + relativedelta(months=1)
                month_end = next_month - relativedelta(days=1)
                if month_end > self.fecha_fin:
                    month_end = self.fecha_fin

                self.env['panelhex.programa.maestro.produccion.mensual'].create({
                    'plan_id': self.id,
                    'date': current_date,
                    'product_id': self.product_id.id,
                })

                current_date = next_month
        except Exception as e:
            _logger.error(f"Error al crear los datos mensuales: {str(e)}")

    def action_generate_production_orders(self):
        self.ensure_one()
        if self.estado != 'confirmado':
            raise UserError("Solo se pueden generar órdenes de producción para programas confirmados.")

        try:
            for monthly_data in self.monthly_data:
                if monthly_data.suggested_replenishment > 0:
                    existing_mo = self.env['mrp.production'].search([
                        ('product_id', '=', self.product_id.id),
                        ('date_planned_start', '=', monthly_data.date),
                        ('origin', '=', f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}")
                    ])
                    if not existing_mo:
                        self.env['mrp.production'].create({
                            'product_id': self.product_id.id,
                            'product_qty': monthly_data.suggested_replenishment,
                            'date_planned_start': monthly_data.date,
                            'origin': f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}",
                        })

            self.write({'estado': 'planificado'})
        except Exception as e:
            _logger.error(f"Error al generar órdenes de producción: {str(e)}")
            raise UserError("Error al generar órdenes de producción. Por favor, revise el registro de errores.")

class ProgramaMaestroProduccionMensual(models.Model):
    _name = 'panelhex.programa.maestro.produccion.mensual'
    _description = 'Datos Mensuales del Programa Maestro de Producción'
    _order = 'date'

    plan_id = fields.Many2one('panelhex.programa.maestro.produccion', string='Programa Maestro', required=True, ondelete='cascade')
    date = fields.Date(string='Mes', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_monthly_data', store=True)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_monthly_data', store=True)
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_monthly_data', store=True)

    @api.depends('plan_id', 'date', 'product_id')
    def _compute_monthly_data(self):
        for record in self:
            try:
                if not record.date or not record.product_id:
                    record.demand_forecast = 0.0
                    record.suggested_replenishment = 0.0
                    record.forecasted_stock = 0.0
                    continue

                start_date = record.date
                end_date = start_date + relativedelta(months=1) - relativedelta(days=1)

                # Calcular demanda pronosticada basada en ventas históricas
                sales = self.env['sale.order.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('order_id.date_order', '>=', start_date - relativedelta(months=3)),
                    ('order_id.date_order', '<', start_date),
                    ('order_id.state', 'in', ['sale', 'done'])
                ])
                total_sales = sum(sales.mapped('product_uom_qty'))
                record.demand_forecast = total_sales / 3 if total_sales else 0.0

                # Obtener stock previsto del mes anterior
                previous_month_data = self.search([
                    ('plan_id', '=', record.plan_id.id),
                    ('date', '<', record.date),
                    ('product_id', '=', record.product_id.id)
                ], order='date desc', limit=1)
                if previous_month_data:
                    previous_stock = previous_month_data.forecasted_stock
                else:
                    # Usar stock actual si no hay datos del mes anterior
                    company_id = self.env.company.id
                    stock_quant = self.env['stock.quant'].read_group(
                        [('product_id', '=', record.product_id.id),
                         ('location_id.usage', '=', 'internal'),
                         ('company_id', '=', company_id)],
                        ['quantity', 'reserved_quantity'],
                        []
                    )
                    if stock_quant:
                        available_quantity = stock_quant[0]['quantity'] - stock_quant[0]['reserved_quantity']
                        previous_stock = available_quantity
                    else:
                        previous_stock = 0.0

                    # Agregar logs de depuración
                    _logger.info(f"Producto: {record.product_id.name}")
                    _logger.info(f"Stock actual (quantity): {stock_quant[0]['quantity'] if stock_quant else 'No data'}")
                    _logger.info(f"Stock reservado (reserved_quantity): {stock_quant[0]['reserved_quantity'] if stock_quant else 'No data'}")
                    _logger.info(f"Stock disponible (available_quantity): {previous_stock}")

                safety_stock = record.plan_id.safety_stock
                record.suggested_replenishment = max(0, record.demand_forecast + safety_stock - previous_stock)

                # Calcular stock previsto
                planned_production = self.env['mrp.production'].search([
                    ('product_id', '=', record.product_id.id),
                    ('date_planned_start', '>=', start_date),
                    ('date_planned_start', '<=', end_date),
                    ('state', 'not in', ['cancel', 'done'])
                ])
                total_planned_production = sum(planned_production.mapped('product_qty'))

                record.forecasted_stock = previous_stock + total_planned_production - record.demand_forecast
            except Exception as e:
                _logger.error(f"Error al calcular los datos mensuales: {str(e)}")
                record.demand_forecast = 0.0
                record.suggested_replenishment = 0.0
                record.forecasted_stock = 0.0

    @api.model
    def create(self, vals):
        if 'date' in vals and isinstance(vals['date'], str):
            try:
                vals['date'] = fields.Date.from_string(vals['date'])
            except ValueError:
                _logger.error(f"Formato de fecha inválido: {vals['date']}")
                vals['date'] = fields.Date.today()
        return super(ProgramaMaestroProduccionMensual, self).create(vals)

    def write(self, vals):
        if 'date' in vals and isinstance(vals['date'], str):
            try:
                vals['date'] = fields.Date.from_string(vals['date'])
            except ValueError:
                _logger.error(f"Formato de fecha inválido: {vals['date']}")
                vals['date'] = fields.Date.today()
        return super(ProgramaMaestroProduccionMensual, self).write(vals)
