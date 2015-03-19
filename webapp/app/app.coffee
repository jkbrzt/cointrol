Router = require 'router'
{LayoutView} = require 'views'
{
    Tickers
    Orders
    Transactions
    Balances
    TradingSessions
    Connection
} = require 'models'


app = new Backbone.Model
app.tickers = new Tickers()
app.balances = new Balances()
app.orders = new Orders()
app.transactions = new Transactions()
app.sessions = new TradingSessions()


PUSH_MAP =
    Ticker: app.tickers
    Balance: app.balances
    Order: app.orders
    Transaction: app.transactions
    TradingSession: app.sessions



app.connection = new Connection()



do ->
    reconnectAttempts = 0

    switchFromOnlineToConnectedInAWhile = _.debounce ->
        if app.connection.getStatus() is Connection.ONLINE
            app.connection.setStatus(Connection.CONNECTED)
    , 2000

    connect = ->

        reconnectAttempts++

        app.socket = _.extend new SockJS('/realtime/changes'),

            onopen: ->
                reconnectAttempts = 0
                app.connection.setStatus(Connection.CONNECTED)
                console.log 'onopen'

            onmessage: (e)->
                console.log e.data
                data = JSON.parse(e.data)

                app.connection.setStatus(Connection.ONLINE)
                switchFromOnlineToConnectedInAWhile()
                return if data.type is 'beacon'

                collection = PUSH_MAP[data.type]
                if not collection
                    console.error('Unknown type', data.type)
                else
                    models = (collection.model::parse(model) for model in data.models)
                    collection.add(models, {merge: yes})

            onclose: ->
                app.connection.setStatus(Connection.OFFLINE)
                timeoutSeconds = Math.min(.5 * reconnectAttempts, 5)
                console.log "onclose; reconnecting in #{timeoutSeconds}s"
                window.setTimeout(connect, timeoutSeconds * 1000)


    connect()


app.router = new Router({app})
app.layout = new LayoutView(el: document.body, app: app)
app.layout.render()

app.tickers.fetch()
app.balances.fetch()

Backbone.history.start(pushState: yes)


module.exports = app
