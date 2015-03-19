exports.config =
# See http://brunch.io/#documentation for docs.
    files:
        javascripts:
            joinTo:
                'js/app.js': /^app/
                'js/vendor.js': /^(bower_components|vendor)/
            order:
                # Files in `vendor` directories are compiled before other files
                # even if they aren't specified in order.before.
                before: [
                    'bower_components/jquery/jquery.js',
                    'bower_components/underscore/underscore.js',
                    'bower_components/backbone/backbone.js'
                ]
        stylesheets:
            defaultExtension: 'sass'
            joinTo: 'css/app.css'
        templates:
            joinTo: 'js/app.js'
