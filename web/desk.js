const el = Object.fromEntries([...document.querySelectorAll('[id]')].map(node => [node.id, node]));
const buttons = [el.apply, el.browse, el.reset];
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function clockLabel(value) {
  const [hour, minute] = value.split(':').map(Number);
  return `${hour % 12 || 12}:${String(minute).padStart(2, '0')} ${hour < 12 ? 'a.m.' : 'p.m.'}`;
}

function minutes(value) {
  const [hour, minute] = value.split(':').map(Number);
  return hour * 60 + minute;
}

function noteLabel(id) {
  return `Note ${String(id).padStart(2, '0')}`;
}

function noteRow(note) {
  const row = document.createElement('li');
  row.className = 'note';
  const head = document.createElement('p');
  head.className = 'note-head';
  const time = document.createElement('span');
  time.className = 'note-time';
  time.textContent = `${noteLabel(note.id)} · ${clockLabel(note.at)} · `;
  head.append(time, note.title);
  const text = document.createElement('p');
  text.textContent = note.text;
  row.append(head, text);
  return row;
}

function updateText(node, value) {
  node.textContent = value;
  node.hidden = !value;
}

function render(data, updated) {
  const { context, recommendation, excluded, notes } = data;
  const until = minutes(context.starts) - minutes(data.as_of);
  el['shift-label'].textContent = updated ? 'Updated shift' : 'Opening shift';
  el['desk-time'].textContent = clockLabel(data.as_of);
  el.booking.textContent = `${context.workshop} · ${context.room} · ${clockLabel(context.starts)} start`;
  el['time-left'].textContent = `${Math.max(0, until)} min`;
  el.person.textContent = recommendation?.person ?? 'Check with the desk';
  el.person.classList.toggle('is-empty', !recommendation);
  updateText(el.location, recommendation?.location ?? '');
  el.why.textContent = recommendation
    ? `${recommendation.person} knows the screens and is available now.`
    : 'The notes don’t confirm a screen helper who is free at a known location.';
  let direction = 'Get a fresh handoff before directing the member.';
  if (recommendation) {
    const { person, location } = recommendation;
    direction = location === context.room
      ? `Ask ${person} in ${location} to help with the slides.`
      : `Find ${person} in ${location} and ask them to help in ${context.room}.`;
  }
  updateText(el.action, direction);

  const refs = recommendation ? Object.values(recommendation.evidence).map(fact => fact.note) : [];
  const evidence = notes.filter(note => refs.includes(note.id)).reverse();
  el.evidence.replaceChildren(...evidence.map(noteRow));
  el['evidence-title'].textContent = recommendation ? 'Why this person' : 'Availability';
  const states = {
    busy: 'is busy',
    'current location unconfirmed': 'has no confirmed location',
    'availability unconfirmed': 'has unconfirmed availability',
  };
  updateText(el.unavailable, excluded.map(({ person, reason, evidence }) =>
    `${person} ${states[reason]}${evidence.note ? ` (${noteLabel(evidence.note)})` : ''}.`
  ).join(' '));
  el['notes-count'].textContent = `All shift notes (${notes.length})`;
  el.notes.replaceChildren(...notes.map(noteRow));
  el.apply.hidden = !data.demo_available || updated;
  el.reset.hidden = !updated;
  el.answer.setAttribute('aria-busy', 'false');
}

async function request(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error ?? 'Couldn’t read the desk data.');
  return payload;
}

async function changeShift(work, updated, initial = false) {
  let nextFocus;
  buttons.forEach(button => { button.disabled = true; });
  el.answer.setAttribute('aria-busy', 'true');
  el.status.removeAttribute('data-error');
  updateText(el.status, initial ? '' : 'Checking the shift notes…');
  try {
    const data = await work();
    render(data, updated);
    if (updated) {
      const latest = data.notes.at(-1);
      updateText(el.status, `${noteLabel(latest.id)} applied. Desk card updated.`);
      nextFocus = el.reset;
    } else {
      updateText(el.status, '');
      if (!initial) nextFocus = el.apply.hidden ? el.browse : el.apply;
    }
    if (!initial && !reducedMotion.matches && window.gsap) {
      window.gsap.fromTo('.answer-body', { y: 8, opacity: 0.7 }, {
        y: 0, opacity: 1, duration: 0.24, ease: 'power2.out', clearProps: 'transform,opacity', overwrite: true,
      });
    }
  } catch (error) {
    el.answer.setAttribute('aria-busy', 'false');
    el.status.setAttribute('data-error', '');
    updateText(el.status, error.message);
    if (initial) {
      el.person.textContent = 'Couldn’t load notes';
      el.person.classList.add('is-empty');
    }
  } finally {
    buttons.forEach(button => { button.disabled = false; });
    nextFocus?.focus({ preventScroll: true });
  }
}

function applyHandoff(notes) {
  const additions = Array.isArray(notes) ? notes : [notes];
  if (!additions.length || additions.some(note => !/^\d{2}:\d{2}$/.test(note?.at))) {
    throw new Error('Enter a shift time in HH:MM for each handoff.');
  }
  const at = ['13:55', ...additions.map(note => note.at)].sort().at(-1);
  return request('/api/desk', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ at, notes }),
  });
}

el.apply.addEventListener('click', () => changeShift(async () => applyHandoff(await request('/minute-40.json')), true));
el.reset.addEventListener('click', () => changeShift(() => request('/api/desk'), false));
el.browse.addEventListener('click', () => el.file.click());
el.file.addEventListener('change', () => {
  const file = el.file.files[0];
  el.file.value = '';
  if (file) changeShift(async () => applyHandoff(JSON.parse(await file.text())), true);
});
changeShift(() => request('/api/desk'), false, true);
