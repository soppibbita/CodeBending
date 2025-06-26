def after_scenario(context, scenario):
    if hasattr(context, 'db') and hasattr(context, 'app'):
        with context.app.app_context():
            context.db.session.remove()
            context.db.drop_all()
    
    if hasattr(context, 'client'):
        context.client = None