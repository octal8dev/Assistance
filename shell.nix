# Этот файл предназначен для использования с командой nix-shell
# для получения интерактивной среды разработки.

{ pkgs ? import <nixpkgs> { channel = "stable-24.05"; } }:

let
  # Define YooMoney package because it's not in nixpkgs by default
  yoomoney-custom = pkgs.python311Packages.buildPythonPackage rec {
    pname = "yoomoney";
    version = "0.1.2";
    
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/a0/15/f664ee5286caba8dd593cd1f40129e828421bf798416732b2f1d47cfedfa/yoomoney-0.1.2.tar.gz";
      sha256 = "dfeb7bc66976d2ea79810f8f7161138c807b47871f9e0fcb949e6813a8e2dcbb";
    };

    propagatedBuildInputs = with pkgs.python311Packages; [
      requests
      pydantic
    ];
  };

  # Определение Python-окружения со всеми пакетами из requirements.txt
  pythonPackages = ps: with ps; [
    amqp
    asgiref
    billiard
    celery
    certifi
    charset-normalizer
    click
    click-plugins
    click-repl
    colorama
    cron-descriptor
    django
    django-celery-beat
    django-cors-headers
    django-filter
    django-timezone-field
    djangorestframework
    djangorestframework-simplejwt
    google-auth
    gunicorn
    idna
    kombu
    packaging
    pillow
    prompt-toolkit
    psycopg2
    pydantic  # Dependency for yoomoney
    pyjwt
    python-crontab
    python-dateutil
    python-decouple
    redis
    requests
    six
    sqlparse
    stripe
    typing-extensions
    tzdata
    urllib3
    vine
    wcwidth
    yoomoney-custom # Add our custom package
  ];
  
  # Создание окружения Python с указанными пакетами
  pythonWithPackages = pkgs.python311.withPackages pythonPackages;

in
  # Определение самой оболочки
  pkgs.mkShell {
    # Пакеты, которые будут доступны в среде
    buildInputs = [
      pythonWithPackages
      pkgs.nodejs_20
      pkgs.nodePackages.npm
      pkgs.postgresql_15
      pkgs.redis
      pkgs.git
      pkgs.wget
      pkgs.docker
      pkgs.docker-compose
    ];

    # Хук, который выполняется при входе в оболочку
    shellHook = ''
      # Установка переменных окружения
      export SECRET_KEY="your-secret-key-change-me-for-local-dev"
      export DEBUG="True"
      export ALLOWED_HOSTS="localhost,127.0.0.1"
      export POSTGRES_DB="octal_assistance"
      export POSTGRES_USER="user"
      export POSTGRES_PASSWORD="password"
      export DATABASE_URL="postgresql://user:password@localhost:5432/octal_assistance"
      export REDIS_URL="redis://localhost:6379/0"
      export PYTHONPATH="$PWD/backend"
      
      echo ""
      echo "### Окружение Nix готово ###"
      echo "Все зависимости (Python, Node.js, Postgres) и переменные окружения установлены."
      echo "Можно выполнять команды, например:"
      echo "python backend/manage.py --help"
      echo "############################"
      echo ""
    '';
}
