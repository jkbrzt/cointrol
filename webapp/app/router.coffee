views = require 'views'
models = require 'models'


module.exports = class Router extends Backbone.Router

    routes:
        '': 'dashboard'

    initialize: (options)->
        @app = options.app

    setView: (viewClass, options)->
        @view?.remove()
        options = _.extend {}, options, {@app}
        @view = new viewClass(options)
        $('#main').append(@view.render().el)

    dashboard: ->
        @setView(views.DashboardPageView, {@app})
