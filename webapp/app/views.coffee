class View extends Backbone.View

    template: null

    constructor: (options)->
        {@app} = options
        @subviews = []
        super options

    render: =>
        template = @getTemplate()
        if template
            @$el.html(template(@getTemplateData()))
        @

    getTemplateData: ->
        @model?.toTemplateData()

    getTemplate: ->
        if @template
            require "templates/#{@template}"

    append: (viewClass, options)=>
        @$el.append(@add(viewClass, options).render().el)

    prepend: (viewClass, options)=>
        @$el.prepend(@add(viewClass, options).render().el)

    add: (viewClass, options)=>
        view = new viewClass(options)
        view.once('remove', @_forgetSubview)
        @subviews.push(view)
        view

    remove: =>
        ###
        - Remove from DOM and unbind DOM events.
        - Remove all listeners bind on this view.
        - Remove all listeners on models this views binds to.
        - Recursivelly call on all `@subviews`

        ###
        @trigger('remove', @)
        super()
        @off()
        @removeSubviews()

    _forgetSubview: (view)=>
        # Forget the subview once it's been destroyed.
        @subviews = _.without(@subviews, view)

    removeSubviews: ->
        for view in @subviews
            view.remove()
        @subviews.length = 0


class ListView extends View
    ###
    Base list view that handles loading more items from the API
    and rendering them, when fully scrolled, etc.

    ###

    itemViewClass: null
    events:
        mousewheel: 'handleScroll'
        DOMMouseScroll: 'handleScroll'

    isEmptyClass: 'is-empty'

    initialize: (options)->
        @$loading = @$('.loading').remove()
        @listenTo @collection, 'reset', @render
        @listenTo @collection, 'add', @addOne
        @listenTo @collection, 'request', @loadingStarted
        @listenTo @collection, 'sync', @loadingEnded

    render: =>
        # Shouldn't be called when some items are already rendered.
        @collection.each @addOne

        @maybeLoadMore()

        # Firefox remembers scroll position for divs after refresh.
        # Could trigger many pages being loaded, so we reset it.
        @$el.scrollTop(0)

        @

    getItemContainer: ->
        @$el

    addOne: (model)=>
        return if model.view
        index = @collection.indexOf(model)
        model.view = @getView(model)
        $item = $(model.view.render().el)
        $item.addClass('item').attr('data-item-id', model.id)

        origScrollTop = @$el.scrollTop()

        if index is 0
            @getItemContainer().prepend($item)
        else
            $item.insertAfter(
                @getItemContainer().find("> .item:eq(#{index - 1})"))

        if origScrollTop and $item.position().top < 0
            # Preserve scroll position to a jumping when scrolled.
            # The calculation is correct, but Chrome still jumps a bit.
            @$el.scrollTop(origScrollTop + $item.outerHeight(yes))

    isFullyScrolled: ->
        @$el.height() + @$el.scrollTop() is @$el.prop('scrollHeight')

    shouldPreventParentScroll: ->
        yes

    handleScroll: (e)=>
        if e?.originalEvent.wheelDeltaY < 0
            # DOWN
            if @isFullyScrolled()
                if @shouldPreventParentScroll()
                    e.preventDefault()
                @maybeLoadMore()
        else
            # UP
            if @shouldPreventParentScroll() and @$el.scrollTop() is 0
                e.preventDefault()

    maybeLoadMore: ->
        ###
        Fetch next page if there is more pages and the list
        has no further items to be scrolled to.

        ###
        if not @isLoading and @collection.hasNext() and @isFullyScrolled()
            @collection.fetchNext()

    loadingStarted: =>
        @isLoading = yes
        @$el.append(@$loading)

    loadingEnded: =>
        @isLoading = no
        @$loading.remove()
        @maybeLoadMore()

    getViewClass: (model)->
        @itemViewClass

    getView: (model)->
        @add(@getViewClass(model), {model})


class LayoutView extends View
    template: 'layout'

    events:
        'click a': 'handleLinkClick'

    render: ->
        super

        window.setInterval(
            ->
                $('[data-date]').each ->
                    $(this).text(moment($(this).data('date')).fromNow())
            , 10 * 1000
        )

        @connection = @add ConnectionView,
            model: @app.connection
            el: @$('#conn-status')
        @connection.render()

        @ticketView = @add TickerView,
            collection: @app.tickers
            el: @$('#ticker')

        @balanceView = @add BalanceView,
            collection: @app.balances
            el: @$('#balance')

        $('html').tooltip(
            container: $('body')
            selector: '[title]'
            placement: 'auto'
        )

        @

    handleLinkClick: (e)=>
        $a = $(e.currentTarget)
        if not $a.attr('target') and not $a.is('.external')
            e.preventDefault()
            url = $a.attr 'href'
            Backbone.history.navigate(url, true)


class TickerView extends View

    template: 'ticker'

    initialize: (options)->
        @title = document.title
        @listenTo @collection, 'add', @render

    render: ->
        @model = @collection.first()
        document.title = "($#{@model.toTemplateData().last}) #{@title}"
        super


class BalanceView extends View

    template: 'balance'

    initialize: (options)->
        @title = document.title
        @listenTo @collection, 'add', @render

    render: ->
        @model = @collection.first()
        super

    getTemplateData: ->

        account_value = @model.get('usd_available')
        account_value += @model.get('btc_available') * app.tickers.first().get('last')
        account_value = @model.templateDataProcessors.usd_available(account_value)

        data = super()
        data.account_value = account_value
        data



class DashboardPageView extends View
    template: 'dashboard_page'

    render: ->

        super

        @add(OrderListView,
            collection: @app.orders
            el: @$('#orders .table-responsive')
        ).render()

        @add(TransactionListView,
            collection: @app.transactions
            el: @$('#transactions .table-responsive')
        ).render()

        @add(SessionListView,
            collection: @app.sessions
            el: @$('#sessions .table-responsive')
        ).render()

        @


class ListItem extends View
    tagName: 'tr'

    initialize: (options)->
        @listenTo(@model, 'change', @render)


class OrderItemView extends ListItem
    template: 'order_item'


class OrderListView extends ListView
    itemViewClass: OrderItemView

    getItemContainer: ->
        @$('tbody:first')


class SessionItemView extends ListItem
    template: 'session_item'

class SessionListView extends ListView
    itemViewClass: SessionItemView

    getItemContainer: ->
        @$('tbody:first')


class TransactionItemView extends ListItem
    template: 'transaction_item'

class TransactionListView extends ListView

    itemViewClass: TransactionItemView

    getItemContainer: ->
        @$('tbody:first')


class ConnectionView extends View

    initialize: (options)->
        super
        @listenTo @model, 'change', @render

    render: =>
        timestamp = @model.get('timestamp')
        @$el.attr
            class: @model.get('status')
            title: "#{timestamp.fromNow()} (#{timestamp.toString()})"
        @


module.exports = {
    LayoutView
    DashboardPageView
}
