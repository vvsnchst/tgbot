from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from models import Vacancy, Resume

def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💼 Я соискатель", callback_data="job_seeker")],
        [InlineKeyboardButton(text="👨‍💻 Я работодатель", callback_data="employer")]
    ])
    return keyboard

def get_job_seeker_menu() -> InlineKeyboardMarkup:
    """Клавиатура меню соискателя"""
    keyboard = [
        [InlineKeyboardButton(text="Создать резюме", callback_data="create_resume")],
        [InlineKeyboardButton(text="Мои резюме", callback_data="my_resumes")],
        [InlineKeyboardButton(text="Поиск вакансий", callback_data="search_vacancies")],
        [InlineKeyboardButton(text="Мои отклики", callback_data="my_applications")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_employer_menu() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Разместить вакансию", callback_data="post_vacancy")],
        [InlineKeyboardButton(text="📋 Мои вакансии", callback_data="my_vacancies")],
        [InlineKeyboardButton(text="📬 Отклики", callback_data="responses")],
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")]
    ])
    return keyboard

def get_vacancies_list_keyboard(vacancies: List[Vacancy]) -> InlineKeyboardMarkup:
    keyboard = []
    for vacancy in vacancies:
        keyboard.append([InlineKeyboardButton(
            text=vacancy.title,
            callback_data=f"view_vacancy_{vacancy.id}"
        )])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="employer")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_vacancies_list_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Вернуться к списку вакансий", callback_data="my_vacancies")],
        [InlineKeyboardButton(text="🗑 Удалить вакансию", callback_data=f"delete_vacancy_{vacancy_id}")]
    ])
    return keyboard

def get_skip_file_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оставить без файла", callback_data="skip_file")]
    ])
    return keyboard

def get_confirm_skip_file_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="confirm_skip_file"),
            InlineKeyboardButton(text="Нет", callback_data="cancel_skip_file")
        ]
    ])
    return keyboard

def get_confirm_delete_vacancy_keyboard(vacancy_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data=f"confirm_delete_vacancy_{vacancy_id}"),
            InlineKeyboardButton(text="Нет", callback_data=f"view_vacancy_{vacancy_id}")
        ]
    ])
    return keyboard

def get_resumes_list_keyboard(resumes):
    keyboard = []
    for resume in resumes:
        keyboard.append([InlineKeyboardButton(
            text=f"{resume.title}",
            callback_data=f"view_resume_{resume.id}"
        )])
    keyboard.append([InlineKeyboardButton(
        text="◀️ Назад в меню",
        callback_data="return_to_main_menu"
    )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_delete_resume_keyboard(resume_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_resume_{resume_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="my_resumes")
        ]
    ])

def get_back_to_resumes_list_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="◀️ Назад к списку резюме",
                callback_data="my_resumes"
            ),
            InlineKeyboardButton(
                text="🗑 Удалить резюме",
                callback_data="delete_resume"
            )
        ]
    ])

def get_vacancy_navigation_keyboard(vacancy_id: int, total_vacancies: int, current_index: int) -> InlineKeyboardMarkup:
    """Клавиатура для навигации по найденным вакансиям"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"prev_vacancy_{current_index}"
        ))
    if current_index < total_vacancies - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"next_vacancy_{current_index}"
        ))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка отклика
    keyboard.append([
        InlineKeyboardButton(
            text="Откликнуться",
            callback_data=f"apply_vacancy_{vacancy_id}"
        )
    ])
    
    # Кнопка возврата в меню
    keyboard.append([
        InlineKeyboardButton(
            text="Вернуться в меню",
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_resume_selection_keyboard(resumes: List[Resume], vacancy_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора резюме при отклике на вакансию"""
    keyboard = []
    
    # Кнопки с резюме
    for resume in resumes:
        keyboard.append([
            InlineKeyboardButton(
                text=resume.title,
                callback_data=f"select_resume_{resume.id}_{vacancy_id}"
            )
        ])
    
    # Кнопка возврата к вакансии
    keyboard.append([
        InlineKeyboardButton(
            text="Вернуться к вакансии",
            callback_data=f"back_to_vacancy_{vacancy_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_application_response_keyboard(application_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для ответа на отклик"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="Пригласить",
                callback_data=f"invite_{application_id}"
            ),
            InlineKeyboardButton(
                text="Отказать",
                callback_data=f"reject_{application_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

__all__ = [
    'get_main_menu',
    'get_employer_menu',
    'get_job_seeker_menu',
    'get_skip_file_keyboard',
    'get_confirm_skip_file_keyboard',
    'get_vacancies_list_keyboard',
    'get_back_to_vacancies_list_keyboard',
    'get_confirm_delete_vacancy_keyboard',
    'get_resumes_list_keyboard',
    'get_back_to_resumes_list_keyboard',
    'get_confirm_delete_resume_keyboard',
    'get_vacancy_navigation_keyboard',
    'get_resume_selection_keyboard',
    'get_application_response_keyboard'
] 