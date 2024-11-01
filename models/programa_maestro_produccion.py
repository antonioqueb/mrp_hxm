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
        programa._create_monthly_data()
        return programa

    def write(self, vals):
        res = super(ProgramaMaestroProduccion, self).write(vals)
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

class ProgramaMaestroProduccionMensual(models.Model):
    _name = 'panelhex.programa.maestro.produccion.mensual'
    _description = 'Datos Mensuales del Programa Maestro de Producción'
    _order = 'date'

    plan_id = fields.Many2one('panelhex.programa.maestro.produccion', string='Programa Maestro', required=True, ondelete='cascade')
    date = fields.Date(string='Mes', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    safety_stock = fields.Float(string='Stock de Seguridad', related='plan_id.safety_stock', store=True, readonly=False)
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_monthly_data', store=True)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_monthly_data', store=True)
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_monthly_data', store=True)
    qty_available = fields.Float(string='Cantidad a mano', compute='_compute_monthly_data', store=True)
    incoming_qty = fields.Float(string='Cantidad entrante', compute='_compute_monthly_data', store=True)
    outgoing_qty = fields.Float(string='Cantidad saliente', compute='_compute_monthly_data', store=True)
    virtual_available = fields.Float(string='Inventario pronosticado', compute='_compute_monthly_data', store=True)

    @api.depends('plan_id', 'date', 'product_id')
    def _compute_monthly_data(self):
        # Ordenar los registros por fecha para asegurar el cálculo secuencial
        records = self.sorted(lambda r: r.date)
        for idx, record in enumerate(records):
            if not record.date or not record.product_id:
                record.demand_forecast = 0.0
                record.suggested_replenishment = 0.0
                record.forecasted_stock = 0.0
                record.qty_available = 0.0
                record.incoming_qty = 0.0
                record.outgoing_qty = 0.0
                record.virtual_available = 0.0
                continue

            # Obtener la fecha actual
            today = fields.Date.context_today(record)

            # Calcular demanda pronosticada basada en ventas históricas de los últimos 3 meses antes de hoy
            sales_start_date = today - relativedelta(months=3)
            sales_end_date = today

            sales = self.env['sale.order.line'].search([
                ('product_id', '=', record.product_id.id),
                ('order_id.date_order', '>=', sales_start_date),
                ('order_id.date_order', '<=', sales_end_date),
                ('order_id.state', 'in', ['sale', 'done'])
            ])
            total_sales = sum(sales.mapped('product_uom_qty'))
            record.demand_forecast = total_sales / 3 if total_sales else 0.0

            # Obtener stock previsto
            if idx == 0:
                # Primer mes, usar inventario pronosticado del producto
                product = record.product_id.with_context(company_id=self.env.company.id, location_id=False)
                previous_stock = product.virtual_available

                # Actualizar campos de stock
                record.qty_available = product.qty_available
                record.incoming_qty = product.incoming_qty
                record.outgoing_qty = product.outgoing_qty
                record.virtual_available = product.virtual_available

                # Agregar logs de depuración
                _logger.info(f"Producto: {record.product_id.display_name}")
                _logger.info(f"A la mano (qty_available): {product.qty_available}")
                _logger.info(f"Entrante (incoming_qty): {product.incoming_qty}")
                _logger.info(f"Saliente (outgoing_qty): {product.outgoing_qty}")
                _logger.info(f"Inventario pronosticado (virtual_available): {product.virtual_available}")
            else:
                # Meses posteriores, usar el stock previsto del mes anterior
                previous_stock = records[idx - 1].forecasted_stock

            # Calcular Reabastecimiento Sugerido sin duplicar el Stock de Seguridad
            net_stock = previous_stock - record.demand_forecast
            record.suggested_replenishment = max(0, record.safety_stock - net_stock)

            # Calcular Stock Previsto
            record.forecasted_stock = net_stock + record.suggested_replenishment

            # Actualizar campos de stock para los registros mensuales posteriores
            record.qty_available = record.forecasted_stock
            record.incoming_qty = record.suggested_replenishment
            record.outgoing_qty = record.demand_forecast
            record.virtual_available = record.forecasted_stock

            # Agregar logs de depuración adicionales
            _logger.info(f"Fecha: {record.date}")
            _logger.info(f"Demanda Pronosticada: {record.demand_forecast}")
            _logger.info(f"Stock Previo: {previous_stock}")
            _logger.info(f"Stock Neto: {net_stock}")
            _logger.info(f"Reabastecimiento Sugerido: {record.suggested_replenishment}")
            _logger.info(f"Stock Previsto: {record.forecasted_stock}")
