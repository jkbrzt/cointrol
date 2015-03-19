processors =
    price: (n)-> parseFloat(n).toFixed(2)
    amount: (n)-> parseFloat(n).toFixed(4)
    amountShort: (n)-> processors.amount(n).replace(/00+$/, '0')
    date: (v)->
        return if not v
        date = new String(v.fromNow())
        date.time = v.valueOf()
        date.full = v.toString()
        date


class Model extends Backbone.Model

    sortDateField: null
    templateDataProcessors: {}

    toTemplateData: ->
        data = @toJSON()
        for k, v of data
            data[k] = @templateDataProcessors[k]?(v) or v
        data

    parse: (response)->
        if @sortDateField
            response[@sortDateField] = moment(response[@sortDateField])
        response


class Collection extends Backbone.Collection

    constructor: (args...)->
        super args...
        @meta = new Backbone.Model()

    comparator: (model)->
        -model.get(model.sortDateField).valueOf()

    parse: (response, options)->
        @meta.set(response.meta)
        response.page

    hasNext: ->
        @meta.get('next') isnt null

    fetchNext: (options)->
        throw 'no next' unless @hasNext()

        if @meta.has('next')
            url = @meta.get('next')
            reset = no
        else
            url = @url
            # We want to trigger 'reset' on first page load.
            reset = yes

        options = _.extend {}, options,
            url: url
            reset: reset
            remove: no

        @fetch options


class Ticker extends Model
    sortDateField: 'timestamp'
    templateDataProcessors:
        timestamp: processors.date
        vwap: processors.price
        last: processors.price
        high: processors.price
        low: processors.price
        bid: processors.price
        ask: processors.price
        volume: processors.amount

class Order extends Model
    sortDateField: 'datetime'
    templateDataProcessors:
        price: processors.price
        amount: processors.amount
        datetime: processors.date
        status_changed: processors.date

    toTemplateData: ->
        _.extend super, icon: @getIconClass()

    parse: (response)->
        response = super
        if response.status_changed
            response.status_changed = moment(response.status_changed)
        response

    getIconClass: ->
        {
            open: 'fa fa-clock-o'
            processed: 'fa fa-check'
            cancelled: 'fa fa-times'
        }[@get('status')]


class Transaction extends Model
    sortDateField: 'datetime'
    templateDataProcessors:
        btc: processors.amount
        usd: processors.amount
        fee: processors.amount
        btc_usd: processors.price
        datetime: processors.date


class Balance extends Model
    sortDateField: 'timestamp'
    templateDataProcessors:
        usd_balance: processors.price
        btc_balance: processors.amountShort
        usd_reserved: processors.amountShort
        btc_reserved: processors.amountShort
        btc_available: processors.amountShort
        usd_available: processors.price
        fee: processors.price
        timestamp: processors.date


class TradingSession extends Model
    sortDateField: 'created'
    templateDataProcessors:
        created: processors.date
        updated: processors.date
        became_active: processors.date
        became_finished: processors.date


class TradingSessions extends Collection
    url: '/api/sessions'
    model: TradingSession

class Tickers extends Collection

    url: '/api/tickers'
    model: Ticker

    comparator: (model)->
        -model.id


class Transactions extends Collection
    url: '/api/transactions'
    model: Transaction


class Orders extends Collection
    url: '/api/orders'
    model: Order


class Balances extends Collection
    url: '/api/balances?limit=10'
    model: Balance


class Connection extends Model

    @OFFLINE = 'offline'
    @CONNECTED = 'connected'
    @ONLINE = 'online'

    defaults:
        status: @OFFLINE

    initialize: (attributes)->
        @set('timestamp', moment())

    getStatus: ->
        @get('status')

    setStatus: (status)->
        @set
            status: status
            timestamp: moment()

    getColor: ->
        @COLORS[@get('status')]


module.exports = {
    Tickers
    Orders
    Transactions
    Balances
    TradingSessions
    Connection
}
