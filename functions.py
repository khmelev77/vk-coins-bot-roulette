def beautiful_name(user_id, vk, link=True):
    data = vk.users.get(user_ids=user_id)
    if link:
        name = "*id%s (%s %s)" % (data[0]['id'], data[0]['first_name'], data[0]['last_name'])
    else:
        name = "%s %s" % (data[0]['first_name'], data[0]['last_name'])
    return name

def convert_list_to_str(list):
    res = ', '.join(str(x) for x in list)

    return res

def digit(num):
    return '{0:,}'.format(num).replace(',', ' ')

def beautiful_time(seconds):
    if seconds <= 59:
        return str(seconds) + " сек. назад"
    elif seconds >= 3600:
        return str(seconds//3600) + " час. назад"
    elif seconds > 59:
        return str(seconds//60) + " мин. назад"