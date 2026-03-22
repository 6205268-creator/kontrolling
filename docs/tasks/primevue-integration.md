# Задача: Подключить PrimeVue к фронтенду

**Дата:** на завтра  
**Цель:** подключить библиотеку PrimeVue и тему Aura, чтобы дальше использовать готовые компоненты (кнопки, формы, таблицы, модалки) и не переписывать позже.

**Статус:** шаги 1–3 выполнены (зависимости установлены, PrimeVue + Aura в `main.ts`, проверка пройдена). Тестовая кнопка удалена. Дальше — по разделу «Что дальше».

---

## Шаг 1. Установить зависимости

Открой терминал, перейди в папку фронтенда и выполни:

```powershell
cd e:\PROGECTS\kontrolling\frontend
npm install primevue @primeuix/themes
```

(В PowerShell одна команда на строку; если используешь `cmd`, то же самое.)

---

## Шаг 2. Подключить PrimeVue в приложении

Открой файл `frontend/src/main.ts` и сделай так:

1. В начале файла добавь импорты (после существующих импортов):

   ```ts
   import PrimeVue from 'primevue/config';
   import Aura from '@primeuix/themes/aura';
   ```

2. Подключи плагин и тему **до** `app.mount('#app')`:

   ```ts
   app.use(PrimeVue, {
     theme: {
       preset: Aura,
       options: {
         darkModeSelector: '[data-theme="dark"]'
       }
     }
   });
   ```

Итоговый `main.ts` должен выглядеть так:

```ts
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import App from './App.vue';
import './style.css';
import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: '[data-theme="dark"]'
    }
  }
});

app.mount('#app');
```

Опция `darkModeSelector` нужна, чтобы PrimeVue подхватывал твою переключалку светлой/тёмной темы (у тебя уже есть `data-theme="dark"` в `MainLayout.vue`).

---

## Шаг 3. Проверить, что всё работает

1. Запусти фронтенд:

   ```powershell
   cd e:\PROGECTS\kontrolling\frontend
   npm run dev
   ```

2. Открой любую страницу (например, «Владельцы»).

3. Временно добавь одну кнопку PrimeVue для проверки:
   - Открой `frontend/src/views/OwnersView.vue`.
   - В начале `<script setup>` добавь: `import Button from 'primevue/button';`
   - В шаблоне рядом с кнопкой «Добавить владельца» добавь: `<Button label="Тест PrimeVue" />`.
   - Сохрани и обнови страницу в браузере: должна появиться вторая кнопка в стиле PrimeVue.

4. Если кнопка отображается без ошибок в консоли — подключение прошло успешно. Кнопку «Тест PrimeVue» потом можно удалить.

---

## Что дальше (не обязательно на завтра)

- Постепенно заменять свои классы (`.btn`, `.form-input`, модалки, таблицы) на компоненты PrimeVue.
- **Сделано:** страница «Владельцы» переведена на PrimeVue: кнопка «Добавить владельца» (Button), поле поиска (InputText), сообщение об ошибке (Message), модалка создания (Dialog), форма — Select + InputText, кнопки в футере Dialog (Отмена / Создать с loading). Таблицу оставили нативной (без DataTable), чтобы не трогать общие компоненты.
- Документация и примеры: [primevue.org](https://primevue.org/).
- Компоненты подключаются по одному: `import Button from 'primevue/button'` и т.д. — так остаётся tree-shaking и не тянется лишнее.

---

## Если что-то пойдёт не так

- Ошибка при `npm install` — проверь, что Node.js и npm обновлены (`node -v`, `npm -v`).
- Ошибка в браузере про тему или стили — убедись, что импорт Aura идёт из `@primeuix/themes/aura`, а не из `primevue/themes`.
- Если захочешь, чтобы агент доделал или проверил — напиши в чате и переключись в режим Agent.
