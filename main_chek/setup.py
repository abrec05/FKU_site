import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="GT_order_processor",  # Имя пакета;
    version="0.1.0",
    author="Закривидорога В. Е.",
    author_email="evzd2003@gmail.com",
    description="Проект для обработки заказов и проверки соответствия ТК",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/my-project",  # ЗАМЕНИТЬ НА ССЫЛКУ МОЕГО ПРОЕКТА
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "numpy>=1.21.0",
        "openpyxl>=3.0.9",
        "pandas>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "order_processor=main:main",
        ],
    },
)
