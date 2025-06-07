from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_session
from models import User, Resume, Vacancy, Application, SearchHistory
from sqlalchemy import select, delete, and_, or_, func
import os
from config import config
from keyboards import (
    get_main_menu,
    get_employer_menu,
    get_job_seeker_menu,
    get_skip_file_keyboard,
    get_confirm_skip_file_keyboard,
    get_vacancies_list_keyboard,
    get_back_to_vacancies_list_keyboard,
    get_confirm_delete_vacancy_keyboard,
    get_resumes_list_keyboard,
    get_back_to_resumes_list_keyboard,
    get_confirm_delete_resume_keyboard,
    get_vacancy_navigation_keyboard,
    get_resume_selection_keyboard,
    get_application_response_keyboard
)

router = Router()

class VacancyStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_company = State()
    waiting_for_salary = State()
    waiting_for_file = State()

class ResumeStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_experience = State()
    waiting_for_file = State()

class SearchVacancy(StatesGroup):
    waiting_for_position = State()

@router.message(Command("menu"))
async def show_menu(message: Message):
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@router.message(Command("start"))
async def cmd_start(message: Message):
    async for session in get_session():
        user = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            new_user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )
            session.add(new_user)
            await session.commit()
            await message.answer(
                "Добро пожаловать в бот поиска работы! 🎉\n\n"
                "Я помогу вам найти работу или сотрудников. Выберите, что вы хотите сделать:",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "С возвращением! 👋\n\n"
                "Выберите действие:",
                reply_markup=get_main_menu()
            )

@router.callback_query(F.data == "job_seeker")
async def process_job_seeker(callback: CallbackQuery):
    await callback.message.edit_text(
        "Меню соискателя:",
        reply_markup=get_job_seeker_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "employer")
async def process_employer(callback: CallbackQuery):
    await callback.message.edit_text(
        "Меню работодателя:",
        reply_markup=get_employer_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "post_vacancy")
async def start_vacancy_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите должность вакансии:")
    await state.set_state(VacancyStates.waiting_for_title)
    await callback.answer()

@router.message(VacancyStates.waiting_for_title)
async def process_vacancy_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание вакансии:")
    await state.set_state(VacancyStates.waiting_for_description)

@router.message(VacancyStates.waiting_for_description)
async def process_vacancy_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите название компании:")
    await state.set_state(VacancyStates.waiting_for_company)

@router.message(VacancyStates.waiting_for_company)
async def process_vacancy_company(message: Message, state: FSMContext):
    await state.update_data(company=message.text)
    await message.answer("Введите зарплату (или 'По договоренности'):")
    await state.set_state(VacancyStates.waiting_for_salary)

@router.message(VacancyStates.waiting_for_salary)
async def process_vacancy_salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await message.answer(
        "Хотите прикрепить файл к вакансии?",
        reply_markup=get_skip_file_keyboard()
    )
    await state.set_state(VacancyStates.waiting_for_file)

@router.callback_query(F.data == "skip_file")
async def confirm_skip_file(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Вы уверены, что хотите создать вакансию без файла?",
        reply_markup=get_confirm_skip_file_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_skip_file")
async def create_vacancy_without_file(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    async for session in get_session():
        vacancy = Vacancy(
            user_id=callback.from_user.id,  # Убедимся, что user_id сохраняется
            title=data["title"],
            company=data["company"],
            salary=data["salary"],
            description=data["description"]
        )
        session.add(vacancy)
        await session.commit()
        
        print(f"Created vacancy: {vacancy.id} for user: {callback.from_user.id}")  # Отладочная информация
        
        await callback.message.edit_text(
            "✅ Вакансия успешно создана!",
            reply_markup=get_employer_menu()
        )
    
    await state.clear()
    await callback.answer()

@router.message(VacancyStates.waiting_for_file)
async def process_vacancy_file(message: Message, state: FSMContext):
    if not message.document and not message.photo:
        await message.answer(
            "Пожалуйста, отправьте файл или фото.",
            reply_markup=get_skip_file_keyboard()
        )
        return
    
    file_id = message.document.file_id if message.document else message.photo[-1].file_id
    file_path = None
    
    if message.document:
        file_path = f"vacancy_files/{message.document.file_name}"
    elif message.photo:
        file_path = f"vacancy_files/photo_{message.message_id}.jpg"
    
    data = await state.get_data()
    
    async for session in get_session():
        vacancy = Vacancy(
            user_id=message.from_user.id,  # Убедимся, что user_id сохраняется
            title=data["title"],
            company=data["company"],
            salary=data["salary"],
            description=data["description"],
            file_id=file_id,
            file_path=file_path
        )
        session.add(vacancy)
        await session.commit()
        
        print(f"Created vacancy with file: {vacancy.id} for user: {message.from_user.id}")  # Отладочная информация
        
        await message.answer(
            "✅ Вакансия успешно создана!",
            reply_markup=get_employer_menu()
        )
    
    await state.clear()

@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
    await callback.answer()

@router.callback_query(F.data == "my_vacancies")
async def show_my_vacancies(callback: CallbackQuery):
    print(f"Showing vacancies for user: {callback.from_user.id}")  # Отладочная информация
    
    async for session in get_session():
        # Получаем все вакансии пользователя
        result = await session.execute(
            select(Vacancy).where(Vacancy.user_id == callback.from_user.id)
        )
        vacancies = result.scalars().all()
        
        print(f"Found {len(vacancies)} vacancies for user {callback.from_user.id}")
        for v in vacancies:
            print(f"Vacancy: {v.id} - {v.title} - User: {v.user_id}")
        
        if not vacancies:
            await callback.message.delete()
            await callback.message.answer(
                "У вас пока нет размещенных вакансий.",
                reply_markup=get_employer_menu()
            )
            return
            
        await callback.message.delete()
        await callback.message.answer(
            "Ваши вакансии:",
            reply_markup=get_vacancies_list_keyboard(vacancies)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("view_vacancy_"))
async def view_vacancy(callback: CallbackQuery, bot: Bot):
    vacancy_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        result = await session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        if not vacancy:
            await callback.message.edit_text(
                "Вакансия не найдена.",
                reply_markup=get_employer_menu()
            )
            return
            
        # Формируем текст сообщения
        text = (
            f"Должность: {vacancy.title}\n"
            f"Компания: {vacancy.company}\n"
            f"Зарплата: {vacancy.salary}\n"
            f"Описание: {vacancy.description}\n"
            f"Дата создания: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_vacancies_list_keyboard(vacancy.id)
        )
        
        # Отправляем файл, если он есть
        if vacancy.file_id:
            try:
                if vacancy.file_path and vacancy.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    await bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=vacancy.file_id,
                        caption=f"Файл вакансии: {vacancy.title}"
                    )
                else:
                    await bot.send_document(
                        chat_id=callback.message.chat.id,
                        document=vacancy.file_id,
                        caption=f"Файл вакансии: {vacancy.title}"
                    )
            except Exception as e:
                print(f"Error sending file: {e}")
                await callback.message.answer(
                    "Не удалось отправить прикрепленный файл."
                )

    await callback.answer()

@router.callback_query(F.data.startswith("delete_vacancy_"))
async def confirm_delete_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split("_")[-1])
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить эту вакансию?",
        reply_markup=get_confirm_delete_vacancy_keyboard(vacancy_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_vacancy_"))
async def delete_vacancy(callback: CallbackQuery, bot: Bot):
    vacancy_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        # Получаем вакансию для удаления файла
        vacancy = await session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = vacancy.scalar_one_or_none()
        
        if vacancy:
            # Удаляем файл, если он есть
            if vacancy.file_path:
                try:
                    if os.path.exists(vacancy.file_path):
                        os.remove(vacancy.file_path)
                        print(f"Файл успешно удален: {vacancy.file_path}")
                    else:
                        print(f"Файл не найден: {vacancy.file_path}")
                except Exception as e:
                    print(f"Ошибка при удалении файла {vacancy.file_path}: {e}")
            
            # Удаляем вакансию из базы данных
            await session.execute(
                delete(Vacancy).where(Vacancy.id == vacancy_id)
            )
            await session.commit()
            print(f"Вакансия успешно удалена из БД: ID {vacancy_id}")
            
            # Удаляем сообщение с подтверждением
            await callback.message.delete()
            
            # Отправляем сообщение об успешном удалении
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text="✅ Вакансия успешно удалена",
                reply_markup=get_employer_menu()
            )
        else:
            await callback.message.edit_text(
                "Вакансия не найдена.",
                reply_markup=get_employer_menu()
            )
    
    await callback.answer()

@router.callback_query(F.data == "create_resume")
async def start_resume_creation(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название вашего резюме (например, 'Python Developer'):"
    )
    await state.set_state(ResumeStates.waiting_for_title)
    await callback.answer()

@router.message(ResumeStates.waiting_for_title)
async def process_resume_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание вашего резюме (образование, навыки и т.д.):")
    await state.set_state(ResumeStates.waiting_for_description)

@router.message(ResumeStates.waiting_for_description)
async def process_resume_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Опишите ваш опыт работы:")
    await state.set_state(ResumeStates.waiting_for_experience)

@router.message(ResumeStates.waiting_for_experience)
async def process_resume_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer(
        "Отправьте файл с вашим резюме (PDF, DOC, изображение) или нажмите кнопку 'Оставить без файла':",
        reply_markup=get_skip_file_keyboard()
    )
    await state.set_state(ResumeStates.waiting_for_file)

@router.callback_query(F.data == "skip_file", ResumeStates.waiting_for_file)
async def skip_resume_file(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Вы уверены, что хотите оставить резюме без файла?",
        reply_markup=get_confirm_skip_file_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_skip_file", ResumeStates.waiting_for_file)
async def confirm_skip_resume_file(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async for session in get_session():
        resume = Resume(
            title=data['title'],
            description=data['description'],
            experience=data['experience'],
            user_id=callback.from_user.id
        )
        session.add(resume)
        await session.commit()
    
    await callback.message.edit_text(
        "✅ Резюме успешно создано!",
        reply_markup=get_job_seeker_menu()
    )
    await state.clear()
    await callback.answer()

@router.message(ResumeStates.waiting_for_file)
async def process_resume_file(message: Message, state: FSMContext, bot: Bot):
    if not message.document and not message.photo:
        await message.answer("Пожалуйста, отправьте файл или нажмите кнопку 'Оставить без файла'")
        return

    data = await state.get_data()
    file_id = None
    file_path = None

    try:
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
            file_path = os.path.join(config.RESUMES_DIR, f"{file_id}_{file_name}")
            # Скачиваем файл
            file = await bot.get_file(file_id)
            await bot.download_file(file.file_path, file_path)
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_path = os.path.join(config.RESUMES_DIR, f"{file_id}.jpg")
            # Скачиваем фото
            file = await bot.get_file(file_id)
            await bot.download_file(file.file_path, file_path)

        async for session in get_session():
            resume = Resume(
                title=data['title'],
                description=data['description'],
                experience=data['experience'],
                user_id=message.from_user.id,
                file_id=file_id,
                file_path=file_path
            )
            session.add(resume)
            await session.commit()

        await message.answer(
            "✅ Резюме успешно создано!",
            reply_markup=get_job_seeker_menu()
        )
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при сохранении файла. Попробуйте еще раз или создайте резюме без файла.",
            reply_markup=get_skip_file_keyboard()
        )
        print(f"Error saving file: {e}")
        return

    await state.clear()

@router.callback_query(F.data == "my_resumes")
async def show_my_resumes(callback: CallbackQuery):
    async for session in get_session():
        # Получаем все резюме пользователя
        result = await session.execute(
            select(Resume).where(Resume.user_id == callback.from_user.id)
        )
        resumes = result.scalars().all()

        if not resumes:
            await callback.message.delete()
            await callback.message.answer(
                "У вас пока нет созданных резюме.",
                reply_markup=get_job_seeker_menu()
            )
            return

        # Формируем список резюме
        await callback.message.delete()
        await callback.message.answer(
            "Ваши резюме:",
            reply_markup=get_resumes_list_keyboard(resumes)
        )
    await callback.answer()

@router.callback_query(F.data.startswith("view_resume_"))
async def view_resume(callback: CallbackQuery, bot: Bot):
    resume_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        result = await session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            await callback.message.edit_text(
                "Резюме не найдено.",
                reply_markup=get_job_seeker_menu()
            )
            return
            
        # Формируем текст сообщения
        text = (
            f"ID: {resume.id}\n"
            f"Название: {resume.title}\n"
            f"Описание: {resume.description}\n"
            f"Опыт работы: {resume.experience}\n"
            f"Дата создания: {resume.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_resumes_list_keyboard()
        )
        
        # Отправляем файл, если он есть
        if resume.file_id:
            try:
                if resume.file_path and resume.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    await bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=resume.file_id,
                        caption=f"Файл резюме: {resume.title}"
                    )
                else:
                    await bot.send_document(
                        chat_id=callback.message.chat.id,
                        document=resume.file_id,
                        caption=f"Файл резюме: {resume.title}"
                    )
            except Exception as e:
                print(f"Error sending file: {e}")
                await callback.message.answer(
                    "Не удалось отправить прикрепленный файл."
                )

    await callback.answer()

@router.callback_query(F.data == "back_to_resumes_list")
async def back_to_resumes_list(callback: CallbackQuery):
    async for session in get_session():
        result = await session.execute(
            select(Resume).where(Resume.user_id == callback.from_user.id)
        )
        resumes = result.scalars().all()
        
        if not resumes:
            await callback.message.edit_text(
                "У вас пока нет созданных резюме.",
                reply_markup=get_job_seeker_menu()
            )
            return
            
        await callback.message.edit_text(
            "Ваши резюме:",
            reply_markup=get_resumes_list_keyboard(resumes)
        )
    await callback.answer()

@router.callback_query(F.data == "delete_resume")
async def delete_resume(callback: CallbackQuery):
    # Получаем ID резюме из предыдущего сообщения
    try:
        # Ищем ID в тексте сообщения
        text_lines = callback.message.text.split('\n')
        for line in text_lines:
            if line.startswith('ID:'):
                resume_id = int(line.split('ID:')[1].strip())
                break
        else:
            raise ValueError("ID не найден в сообщении")
            
    except (IndexError, ValueError) as e:
        print(f"Error parsing resume ID: {e}")
        await callback.message.edit_text(
            "Ошибка: не удалось определить резюме",
            reply_markup=get_job_seeker_menu()
        )
        return
    
    await callback.message.edit_text(
        "Вы уверены, что хотите удалить это резюме?",
        reply_markup=get_confirm_delete_resume_keyboard(resume_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_resume_"))
async def confirm_delete_resume(callback: CallbackQuery):
    try:
        resume_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.message.edit_text(
            "Ошибка: неверный ID резюме",
            reply_markup=get_job_seeker_menu()
        )
        return
    
    async for session in get_session():
        # Получаем резюме
        result = await session.execute(
            select(Resume).where(
                and_(
                    Resume.id == resume_id,
                    Resume.user_id == callback.from_user.id
                )
            )
        )
        resume = result.scalar_one_or_none()

        if not resume:
            await callback.message.edit_text(
                "Ошибка: резюме не найдено или у вас нет прав на его удаление",
                reply_markup=get_job_seeker_menu()
            )
            return

        # Удаляем файл, если он есть
        if resume.file_path and os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")

        # Удаляем резюме из базы данных
        await session.delete(resume)
        await session.commit()

        # Показываем обновленный список резюме
        result = await session.execute(
            select(Resume).where(Resume.user_id == callback.from_user.id)
        )
        resumes = result.scalars().all()
        
        if not resumes:
            await callback.message.edit_text(
                "✅ Резюме успешно удалено!\nУ вас больше нет резюме.",
                reply_markup=get_job_seeker_menu()
            )
        else:
            await callback.message.edit_text(
                "✅ Резюме успешно удалено!\nВаши резюме:",
                reply_markup=get_resumes_list_keyboard(resumes)
            )

    await callback.answer()

@router.callback_query(F.data == "search_vacancies")
async def search_vacancies(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите название вакансии для поиска:"
    )
    await state.set_state(SearchVacancy.waiting_for_position)

@router.message(SearchVacancy.waiting_for_position)
async def process_vacancy_search(message: Message, state: FSMContext):
    search_title = message.text.strip()
    
    async for session in get_session():
        # Ищем вакансии по названию
        result = await session.execute(
            select(Vacancy).where(
                Vacancy.title.ilike(f"%{search_title}%")
            )
        )
        vacancies = result.scalars().all()
        
        if not vacancies:
            await message.answer(
                "Вакансии не найдены. Попробуйте изменить параметры поиска.",
                reply_markup=get_job_seeker_menu()
            )
            return
        
        # Сохраняем найденные вакансии в состоянии
        vacancy_ids = [v.id for v in vacancies]
        await state.update_data(found_vacancies=vacancy_ids)
        
        # Показываем первую вакансию
        vacancy = vacancies[0]
        await message.answer(
            f"Должность: {vacancy.title}\n"
            f"Компания: {vacancy.company}\n"
            f"Зарплата: {vacancy.salary}\n"
            f"Описание: {vacancy.description}\n"
            f"Дата создания: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=get_vacancy_navigation_keyboard(vacancy.id, len(vacancies), 0)
        )
        
        # Отправляем файл, если он есть
        if vacancy.file_id:
            try:
                if vacancy.file_path and vacancy.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    await message.answer_photo(
                        photo=vacancy.file_id,
                        caption=f"Файл вакансии: {vacancy.title}"
                    )
                else:
                    await message.answer_document(
                        document=vacancy.file_id,
                        caption=f"Файл вакансии: {vacancy.title}"
                    )
            except Exception as e:
                print(f"Error sending file: {e}")
                await message.answer(
                    "Не удалось отправить прикрепленный файл."
                )

@router.callback_query(F.data.startswith(("prev_vacancy_", "next_vacancy_")))
async def navigate_vacancies(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    action = parts[1]
    current_index = int(parts[2])
    
    # Получаем сохраненные данные
    data = await state.get_data()
    vacancy_ids = data.get("found_vacancies", [])
    
    if not vacancy_ids:
        await callback.message.delete()
        await callback.message.answer(
            "Вакансии не найдены. Пожалуйста, выполните поиск заново.",
            reply_markup=get_job_seeker_menu()
        )
        return
    
    # Определяем новый индекс
    new_index = current_index - 1 if action == "prev" else current_index + 1
    
    if 0 <= new_index < len(vacancy_ids):
        async for session in get_session():
            result = await session.execute(
                select(Vacancy).where(Vacancy.id == vacancy_ids[new_index])
            )
            vacancy = result.scalar_one_or_none()
            
            if vacancy:
                await callback.message.delete()
                await callback.message.answer(
                    f"Должность: {vacancy.title}\n"
                    f"Компания: {vacancy.company}\n"
                    f"Зарплата: {vacancy.salary}\n"
                    f"Описание: {vacancy.description}\n"
                    f"Дата создания: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}",
                    reply_markup=get_vacancy_navigation_keyboard(vacancy.id, len(vacancy_ids), new_index)
                )
                
                # Отправляем файл, если он есть
                if vacancy.file_id:
                    try:
                        if vacancy.file_path and vacancy.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                            await callback.bot.send_photo(
                                chat_id=callback.message.chat.id,
                                photo=vacancy.file_id,
                                caption=f"Файл вакансии: {vacancy.title}"
                            )
                        else:
                            await callback.bot.send_document(
                                chat_id=callback.message.chat.id,
                                document=vacancy.file_id,
                                caption=f"Файл вакансии: {vacancy.title}"
                            )
                    except Exception as e:
                        print(f"Error sending file: {e}")
                        await callback.message.answer(
                            "Не удалось отправить прикрепленный файл."
                        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("apply_vacancy_"))
async def show_resume_selection(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[-1])
    print(f"Applying for vacancy: {vacancy_id}")  # Отладочная информация
    
    async for session in get_session():
        # Получаем резюме пользователя
        result = await session.execute(
            select(Resume).where(Resume.user_id == callback.from_user.id)
        )
        resumes = result.scalars().all()
        
        print(f"Found {len(resumes)} resumes for user {callback.from_user.id}")  # Отладочная информация
        
        if not resumes:
            await callback.message.edit_text(
                "У вас нет резюме для отклика. Создайте резюме и попробуйте снова.",
                reply_markup=get_job_seeker_menu()
            )
            return
        
        await callback.message.edit_text(
            "Выберите резюме для отклика:",
            reply_markup=get_resume_selection_keyboard(resumes, vacancy_id)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("select_resume_"))
async def submit_application(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    resume_id = int(parts[2])
    vacancy_id = int(parts[3])
    
    print(f"Submitting application: resume {resume_id} for vacancy {vacancy_id}")  # Отладочная информация
    
    async for session in get_session():
        # Получаем вакансию и резюме
        result = await session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        result = await session.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not vacancy or not resume:
            await callback.message.edit_text(
                "Вакансия или резюме не найдены.",
                reply_markup=get_job_seeker_menu()
            )
            return
        
        # Создаем отклик
        application = Application(
            user_id=callback.from_user.id,
            vacancy_id=vacancy_id,
            resume_id=resume_id,
            status="new"
        )
        session.add(application)
        await session.commit()
        
        print(f"Created application: {application.id}")  # Отладочная информация
        
        # Уведомляем работодателя
        await callback.bot.send_message(
            chat_id=vacancy.user_id,
            text=f"На вашу вакансию '{vacancy.title}' пришел отклик!"
        )
        
        # Отправляем работодателю информацию о резюме
        resume_text = (
            f"Резюме соискателя:\n"
            f"Название: {resume.title}\n"
            f"Описание: {resume.description}\n"
            f"Опыт работы: {resume.experience}\n"
            f"Дата создания: {resume.created_at.strftime('%d.%m.%Y %H:%M')}"
        )
        await callback.bot.send_message(
            chat_id=vacancy.user_id,
            text=resume_text,
            reply_markup=get_application_response_keyboard(application.id)
        )
        
        # Отправляем файл резюме, если он есть
        if resume.file_id:
            try:
                if resume.file_path and resume.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    await callback.bot.send_photo(
                        chat_id=vacancy.user_id,
                        photo=resume.file_id,
                        caption=f"Файл резюме: {resume.title}"
                    )
                else:
                    await callback.bot.send_document(
                        chat_id=vacancy.user_id,
                        document=resume.file_id,
                        caption=f"Файл резюме: {resume.title}"
                    )
            except Exception as e:
                print(f"Error sending resume file: {e}")
                await callback.bot.send_message(
                    chat_id=vacancy.user_id,
                    text="Не удалось отправить прикрепленный файл резюме."
                )
        
        await callback.message.edit_text(
            "✅ Отклик успешно отправлен!",
            reply_markup=get_job_seeker_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_application(callback: CallbackQuery, state: FSMContext):
    application_id = int(callback.data.split("_")[1])
    
    async for session in get_session():
        # Получаем информацию об отклике
        result = await session.execute(
            select(Application, Vacancy)
            .join(Vacancy)
            .where(Application.id == application_id)
        )
        application_data = result.first()
        
        if not application_data:
            await callback.message.edit_text(
                "Отклик не найден.",
                reply_markup=get_employer_menu()
            )
            return
        
        application, vacancy = application_data
        
        # Обновляем статус отклика
        application.status = "rejected"
        await session.commit()
        
        # Уведомляем соискателя
        await callback.bot.send_message(
            chat_id=application.user_id,
            text=f"К сожалению, вам отказано в вакансии '{vacancy.title}'."
        )
        
        # Уведомляем работодателя
        await callback.message.edit_text(
            f"Вы отказали соискателю в вакансии '{vacancy.title}'."
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("invite_"))
async def invite_application(callback: CallbackQuery, state: FSMContext):
    application_id = int(callback.data.split("_")[1])
    
    async for session in get_session():
        # Получаем информацию об отклике
        result = await session.execute(
            select(Application, Vacancy)
            .join(Vacancy)
            .where(Application.id == application_id)
        )
        application_data = result.first()
        
        if not application_data:
            await callback.message.edit_text(
                "Отклик не найден.",
                reply_markup=get_employer_menu()
            )
            return
        
        application, vacancy = application_data
        
        # Обновляем статус отклика
        application.status = "invited"
        await session.commit()
        
        # Получаем информацию о работодателе
        employer = await callback.bot.get_chat(vacancy.user_id)
        
        # Уведомляем соискателя
        await callback.bot.send_message(
            chat_id=application.user_id,
            text=(
                f"Поздравляем! Вас пригласили на вакансию '{vacancy.title}'.\n"
                f"Свяжитесь с работодателем: @{employer.username}"
            )
        )
        
        # Уведомляем работодателя
        applicant = await callback.bot.get_chat(application.user_id)
        await callback.message.edit_text(
            f"Вы пригласили соискателя на вакансию '{vacancy.title}'.\n"
            f"Свяжитесь с соискателем: @{applicant.username}"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("back_to_vacancy_"))
async def back_to_vacancy(callback: CallbackQuery, state: FSMContext):
    vacancy_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        result = await session.execute(
            select(Vacancy).where(Vacancy.id == vacancy_id)
        )
        vacancy = result.scalar_one_or_none()
        
        if vacancy:
            await callback.message.edit_text(
                f"Должность: {vacancy.title}\n"
                f"Компания: {vacancy.company}\n"
                f"Зарплата: {vacancy.salary}\n"
                f"Описание: {vacancy.description}\n"
                f"Дата создания: {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_vacancy_navigation_keyboard(vacancy.id, 1, 0)
            )
            
            # Отправляем файл, если он есть
            if vacancy.file_id:
                try:
                    if vacancy.file_path and vacancy.file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        await callback.bot.send_photo(
                            chat_id=callback.message.chat.id,
                            photo=vacancy.file_id,
                            caption=f"Файл вакансии: {vacancy.title}"
                        )
                    else:
                        await callback.bot.send_document(
                            chat_id=callback.message.chat.id,
                            document=vacancy.file_id,
                            caption=f"Файл вакансии: {vacancy.title}"
                        )
                except Exception as e:
                    print(f"Error sending file: {e}")
                    await callback.message.answer(
                        "Не удалось отправить прикрепленный файл."
                    )
    
    await callback.answer()

@router.callback_query(F.data == "return_to_main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_job_seeker_menu()
    )
    await callback.answer() 