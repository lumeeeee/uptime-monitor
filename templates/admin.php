<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Админка уведомлений</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>

<h1>Telegram-уведомления</h1>
<p>Для сохранения требуется секретная фраза</p>

{% for url, chat_id in sites %}
<form method="post" style="margin-bottom:20px;">
  <strong>{{ url }}</strong><br><br>

  <input type="hidden" name="url" value="{{ url }}">

  <input name="chat_id" placeholder="Telegram chat_id" value="{{ chat_id or '' }}" required>
  <br><br>

  <input name="secret" type="password" placeholder="Секретная фраза" required>
  <br><br>

  <button type="submit">Сохранить</button>
</form>
<hr>
{% endfor %}

</body>
</html>
