def user_can_alter_resource(user, resource, allowed_users=None):
    is_owner = resource.get_created_by_user() == user
    is_in_allowed_users = allowed_users.filter(
        account=user
    )

    return is_owner or is_in_allowed_users
