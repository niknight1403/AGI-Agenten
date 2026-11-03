CYAN = "#00e5ff"
def createStyles(**overrides):
    styles = {"accent_color": CYAN, "blur": 16, "wide": {"background": "#101820"}}
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(styles.get(key), dict):
            styles[key] = {**styles[key], **value}
        else:
            styles[key] = value
    return styles
