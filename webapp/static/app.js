// Letter workspace: the student form, then a chat that revises the letter.
// State lives in sessionStorage so a refresh or a trip to the writing style page doesn't lose the letter.

const STORAGE_KEY = 'lor-workspace';

const FIELD_LABELS = {
    name: 'Name',
    pronouns: 'Pronouns',
    area_of_interest: 'Area of interest',
    year: 'Year',
    graduation_date: 'Graduation date',
    academic_characteristics: 'Academic characteristics',
    social_emotional_characteristics: 'Social/emotional characteristics',
    other_notable_aspects: 'Other notable aspects',
    post_secondary_goals: 'Post-secondary goals',
    suitability_for_goals: 'Why they are well suited',
    angelica_instructions: 'Special instructions',
};

const $ = (id) => document.getElementById(id);

const formView = $('formView');
const workspace = $('workspace');
const studentForm = $('studentForm');
const generateBtn = $('generateBtn');
const formError = $('formError');
const newLetterBtn = $('newLetterBtn');
const chatLog = $('chatLog');
const chatForm = $('chatForm');
const chatMessage = $('chatMessage');
const sendBtn = $('sendBtn');
const letterText = $('letterText');
const letterSheet = letterText.parentElement;

// { student, versions: [letter, ...], current: index, messages: [{role, content, local?, error?, letterVersion?, suggestion?}] }
let state = null;
let chatBusy = false;

function loadState() {
    try {
        return JSON.parse(sessionStorage.getItem(STORAGE_KEY));
    } catch {
        return null;
    }
}

function saveState() {
    try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
        // Storage unavailable (private mode, quota); the page still works for this visit
    }
}

async function postJSON(url, body) {
    const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
}

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

/* ---------- Views ---------- */

function showForm() {
    workspace.hidden = true;
    newLetterBtn.hidden = true;
    formView.hidden = false;
    document.title = 'New letter · Recommendation Letters';
}

function showWorkspace() {
    formView.hidden = true;
    workspace.hidden = false;
    newLetterBtn.hidden = false;
    document.title = `${state.student.name} · Recommendation Letters`;
    renderStudentDetails();
    renderLetter();
    renderChat();
    // On phones the letter is above the chat; focusing the chat would scroll past it
    if (window.matchMedia('(min-width: 901px)').matches) chatMessage.focus();
}

/* ---------- Step 1: generate the first draft ---------- */

studentForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const student = {};
    for (const field of Object.keys(FIELD_LABELS)) {
        student[field] = studentForm.elements[field].value.trim();
    }

    formError.hidden = true;
    generateBtn.disabled = true;
    generateBtn.replaceChildren(el('span', 'spinner'), 'Writing the first draft…');

    try {
        const {letter} = await postJSON('/api/generate', {student});
        state = {
            student,
            versions: [letter],
            current: 0,
            messages: [{
                role: 'assistant',
                local: true,
                content: `Here's a first draft for ${student.name}. Tell me what you'd like changed (tone, length, a detail to add or cut) and I'll revise it.`,
            }],
        };
        saveState();
        showWorkspace();
    } catch (err) {
        formError.textContent = err.message;
        formError.hidden = false;
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate letter';
    }
});

// Made-up student for trying the app out quickly
const TEST_STUDENT = {
    name: 'Maria Santos',
    pronouns: 'she/her',
    area_of_interest: 'Political Science',
    year: 'Senior',
    graduation_date: 'June 2027',
    academic_characteristics: 'Consistently one of the strongest students in Global History. 92 GPA. Asks thoughtful questions and connects historical events to current issues. Wrote an excellent DBQ essay on the causes of the French Revolution.',
    social_emotional_characteristics: 'Quiet at first but grew into a confident leader. Kind and patient with classmates, often helps others understand difficult readings. Handles setbacks calmly.',
    other_notable_aspects: 'Captain of the debate team. Works part-time at her family\'s bakery on weekends. First in her family to apply to college.',
    post_secondary_goals: 'Wants to study political science and eventually go to law school to work in immigration law.',
    suitability_for_goals: 'Strong reader and writer, persuasive speaker from debate, and a deep personal commitment to helping immigrant families like her own.',
    angelica_instructions: '',
};

$('fillTestBtn').addEventListener('click', () => {
    for (const [field, value] of Object.entries(TEST_STUDENT)) {
        studentForm.elements[field].value = value;
    }
});

newLetterBtn.addEventListener('click', () => {
    if (!confirm('Start a new letter? The current letter and chat will be cleared, so copy or download it first if you need it.')) return;
    sessionStorage.removeItem(STORAGE_KEY);
    state = null;
    studentForm.reset();
    showForm();
    window.scrollTo(0, 0);
});

/* ---------- Letter panel ---------- */

function renderStudentDetails() {
    const list = $('studentDetails');
    list.replaceChildren();
    for (const [field, label] of Object.entries(FIELD_LABELS)) {
        if (!state.student[field]) continue;
        list.append(el('dt', '', label), el('dd', '', state.student[field]));
    }
}

function renderLetter() {
    const total = state.versions.length;
    $('letterTitle').textContent = `Letter for ${state.student.name}`;
    letterText.value = state.versions[state.current];
    $('versionLabel').textContent = `Version ${state.current + 1} of ${total}`;
    $('prevVersion').disabled = state.current === 0;
    $('nextVersion').disabled = state.current === total - 1;
}

function goToVersion(index) {
    state.current = Math.max(0, Math.min(index, state.versions.length - 1));
    saveState();
    renderLetter();
}

function flashLetter() {
    letterSheet.classList.remove('updated');
    void letterSheet.offsetWidth; // restart the animation
    letterSheet.classList.add('updated');
}

$('prevVersion').addEventListener('click', () => goToVersion(state.current - 1));
$('nextVersion').addEventListener('click', () => goToVersion(state.current + 1));

// Manual edits change the version being viewed
letterText.addEventListener('input', () => {
    state.versions[state.current] = letterText.value;
    saveState();
});

$('copyBtn').addEventListener('click', async (e) => {
    const button = e.currentTarget;
    try {
        await navigator.clipboard.writeText(letterText.value);
    } catch {
        letterText.select();
        document.execCommand('copy');
    }
    button.textContent = 'Copied ✓';
    setTimeout(() => { button.textContent = 'Copy'; }, 2000);
});

$('downloadBtn').addEventListener('click', () => {
    const name = state.student.name.replace(/[\\/:*?"<>|]+/g, '').trim() || 'Letter';
    const blob = new Blob([letterText.value], {type: 'text/plain;charset=utf-8'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${name}.txt`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});

/* ---------- Chat ---------- */

function renderChat() {
    chatLog.replaceChildren(...state.messages.map(messageElement));
    if (chatBusy) {
        const typing = el('div', 'msg msg-assistant typing');
        const bubble = el('div', 'bubble');
        bubble.append(el('span'), el('span'), el('span'));
        typing.append(bubble);
        chatLog.append(typing);
    }
    chatLog.scrollTop = chatLog.scrollHeight;
}

function messageElement(msg) {
    const wrap = el('div', `msg msg-${msg.role}${msg.error ? ' msg-error' : ''}`);
    wrap.append(el('div', 'bubble', msg.content));

    if (msg.letterVersion !== undefined) {
        const chip = el('button', 'version-chip', `Letter updated · Version ${msg.letterVersion + 1}`);
        chip.type = 'button';
        chip.title = 'Show this version';
        chip.addEventListener('click', () => goToVersion(msg.letterVersion));
        wrap.append(chip);
    }

    if (msg.suggestion) wrap.append(suggestionElement(msg));
    return wrap;
}

function suggestionElement(msg) {
    const suggestion = msg.suggestion;

    if (suggestion.status === 'saved') {
        const done = el('div', 'suggestion-done saved', '✓ Added to your writing style · ');
        const link = el('a', '', 'View');
        link.href = '/style';
        done.append(link);
        return done;
    }
    if (suggestion.status === 'dismissed') {
        return el('div', 'suggestion-done dismissed', 'Not added to your writing style');
    }

    const card = el('div', 'suggestion');
    card.append(el('div', 'suggestion-title', 'Add this to your writing style?'));

    const input = el('textarea');
    input.rows = 2;
    input.value = suggestion.text;
    input.setAttribute('aria-label', 'Writing style note');
    input.addEventListener('input', () => {
        suggestion.text = input.value;
        saveState();
    });

    const actions = el('div', 'suggestion-actions');
    const addBtn = el('button', 'btn btn-primary btn-sm', 'Add to writing style');
    addBtn.type = 'button';
    const dismissBtn = el('button', 'btn btn-ghost btn-sm', 'No thanks');
    dismissBtn.type = 'button';
    actions.append(addBtn, dismissBtn);

    const error = el('div', 'suggestion-error');
    error.hidden = true;

    addBtn.addEventListener('click', async () => {
        addBtn.disabled = dismissBtn.disabled = true;
        error.hidden = true;
        try {
            await postJSON('/api/style/notes', {note: input.value});
            suggestion.status = 'saved';
            saveState();
            card.replaceWith(suggestionElement(msg));
        } catch (err) {
            error.textContent = err.message;
            error.hidden = false;
            addBtn.disabled = dismissBtn.disabled = false;
        }
    });

    dismissBtn.addEventListener('click', () => {
        suggestion.status = 'dismissed';
        saveState();
        card.replaceWith(suggestionElement(msg));
    });

    card.append(input, actions, error);
    return card;
}

function setChatBusy(busy) {
    chatBusy = busy;
    sendBtn.disabled = busy;
    renderChat();
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatMessage.value.trim();
    if (!text || chatBusy) return;

    // Send the conversation so far; local notes (the intro, errors) never went to the model
    const history = state.messages
        .filter((m) => !m.local)
        .map(({role, content}) => ({role, content}));

    state.messages.push({role: 'user', content: text});
    chatMessage.value = '';
    resizeChatInput();
    setChatBusy(true);

    try {
        const data = await postJSON('/api/chat', {
            student: state.student,
            letter: letterText.value,
            history,
            message: text,
        });
        const reply = {role: 'assistant', content: data.reply || 'Done.'};
        if (data.letter) {
            state.versions.push(data.letter);
            state.current = state.versions.length - 1;
            reply.letterVersion = state.current;
            renderLetter();
            flashLetter();
        }
        if (data.style_suggestion) {
            reply.suggestion = {text: data.style_suggestion, status: 'pending'};
        }
        state.messages.push(reply);
    } catch (err) {
        // Drop the unanswered message so the history sent to the model stays user/assistant pairs,
        // and put the text back so it can be resent
        state.messages.pop();
        chatMessage.value = text;
        resizeChatInput();
        state.messages.push({role: 'assistant', local: true, error: true, content: `Something went wrong: ${err.message}`});
    }

    saveState();
    setChatBusy(false);
    chatMessage.focus();
});

chatMessage.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

function resizeChatInput() {
    chatMessage.style.height = 'auto';
    chatMessage.style.height = `${Math.min(chatMessage.scrollHeight + 2, 260)}px`;
}

chatMessage.addEventListener('input', resizeChatInput);

/* ---------- Start ---------- */

state = loadState();
if (state && state.student && state.versions && state.versions.length) {
    showWorkspace();
} else {
    state = null;
    showForm();
}
