def apply_command(inst, message, command, arguments):
    if command == "cookie":
        target = inst.get_target(message)
        if len(arguments) > 0:
            messages = [{"target": target, "content": f"Congratulations {' '.join(arguments)}, you deserve a cookie ! 🍪"}]
        else:
            messages = []
        inst.logger.info(messages)
        return {"messages": messages}