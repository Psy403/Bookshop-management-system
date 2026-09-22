def record_activity(request, description, action=None):
    request.activity_log_description = description
    if action:
        request.activity_log_action = action
