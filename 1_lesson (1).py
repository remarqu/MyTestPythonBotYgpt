from yandexgpt import talk_to_yandex_gpt

messages = []

while True:
  if not messages:
    print('Введите сообщение:')
  else:
    print('Введите следующее сообщение:')

  user_input = input()

  if user_input.strip() == '/reset':
    messages = []
    print("Диалог сброшен. Начните заново.")
    continue
  
  messages.append({
    'role': 'user',
    'text': user_input
  })
  answer = talk_to_yandex_gpt(messages)
  messages.append({
    'role': 'assistant',
    'text': answer
  })
  print(answer)