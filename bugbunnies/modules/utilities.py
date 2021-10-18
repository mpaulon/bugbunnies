def apply_command(inst, message, command, arguments):
    if command == "join" and message.get("type") == "privmsg":
        if len(arguments) > 0:
            return {"join": arguments}
        else:
            return {}