# Общая информация

Этот проект представляет собой решение для задачи "Дрон-инспектор" созданное командой GenericBoys

# Оговорка разработчика и условия использования

Применять только в учебных целях. Данный код может содержать ошибки, авторы не несут никакой ответственности за любые последствия использования этого кода.
Условия использования и распространения - MIT лицензия (см. файл LICENSE).
## Отчёт

см. [Отчет](report.md)

## Настройка и запуск

Предполагается, что настройка и подготовка хостовой и гостевой машины были осуществлены в соответствии с инструкциями, приведенными в подготовительном курсе <https://stepik.org/course/133991/promo>.

### Системные требования

Данный пример разработан и проверен на ОС Ubuntu 22.04, авторы предполагают, что без каких-либо изменений этот код может работать на любых Debian-подобных OS, для других Linux систем. Для MAC OS как минимум необходимо использовать другой менеджер пакетов. В Windows необходимо самостоятельно установить необходимое ПО или воспользоваться виртуальной машиной с Ubuntu (также можно использовать WSL версии не ниже 2).

### Используемое ПО

Стандартный способ запуска демо-версии предполагает наличие установленного пакета *docker*, а также *docker-compose*. Для автоматизации типовых операций используется утилита *make*, хотя можно обойтись и без неё, вручную выполняя соответствующие команды из файла Makefile в командной строке.

Другое используемое ПО (в Ubuntu будет установлено автоматически, см. следующий раздел):

- python (желательно версия не ниже 3.8)
- pipenv (для виртуальных окружений python)

Для работы с кодом примера рекомендуется использовать VS Code или PyCharm.

В случае использования VS Code следует установить расширения

- REST client
- Docker
- Python

### Настройка окружения и запуск примера

Подразумевается наличие развернутой по предоставленному образцу машины с установленным и настроенным ПО, например, docker и docker-compose, с выбранным интерпретатором (детальные инструкции по настройке среды разработки представлены в подготовительном курсе, ссылка на который приведена выше).

Для запуска примера:

```chmod -R 777 generic-drone``

``` make all```

просмотр логов: 

```make logs```

тестирование (будет запущен тестовый сценарий проверки работы основного функционала системы)

``` make test ```

завершение работы:

```make clean```