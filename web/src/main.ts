import './style.css';
import { PriorEditor } from './editor';

const editor = new PriorEditor(document.querySelector<SVGSVGElement>('#prior-editor')!);
const form = document.querySelector<HTMLFormElement>('#synthesis-form')!;
const intent = document.querySelector<HTMLTextAreaElement>('#intent')!;
const submit = document.querySelector<HTMLButtonElement>('#synthesize')!;
const resample = document.querySelector<HTMLButtonElement>('#resample')!;
const copy = document.querySelector<HTMLButtonElement>('#copy')!;
const output = document.querySelector<HTMLElement>('#output')!;
const state = document.querySelector<HTMLElement>('#output-state')!;
const error = document.querySelector<HTMLElement>('#error')!;
let utterance = '';
let busy = false;

async function synthesize() {
  if (busy || !intent.value.trim()) { intent.focus(); return; }
  busy = true;
  submit.disabled = true;
  resample.disabled = true;
  state.textContent = 'SYNTHESIS IN PROGRESS';
  error.hidden = true;
  try {
    const response = await fetch(new URL('api/synthesize', new URL('./', location.href)), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ intent: intent.value.trim(), prior: editor.payload() }),
    });
    if (!response.ok) throw new Error('Synthesis is temporarily unavailable. Please re-submit the intent.');
    const data: unknown = await response.json();
    if (typeof data !== 'object' || data === null || !('utterance' in data) || typeof data.utterance !== 'string') throw new Error('The synthesis response could not be resolved.');
    utterance = data.utterance;
    const paragraph = document.createElement('p');
    paragraph.textContent = utterance;
    output.replaceChildren(paragraph);
    state.textContent = 'SYNTHESIS COMPLETE';
    copy.disabled = false;
  } catch (failure) {
    error.textContent = failure instanceof Error ? failure.message : 'Synthesis is temporarily unavailable.';
    error.hidden = false;
    state.textContent = 'SYNTHESIS UNAVAILABLE';
  } finally {
    busy = false;
    submit.disabled = false;
    resample.disabled = !utterance;
  }
}

form.addEventListener('submit', event => { event.preventDefault(); void synthesize(); });
resample.addEventListener('click', () => void synthesize());
copy.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(utterance);
    copy.textContent = 'Utterance copied';
    window.setTimeout(() => { copy.textContent = 'Copy utterance ⧉'; }, 1800);
  } catch {
    error.textContent = 'Clipboard access is unavailable. Select the utterance to copy it.';
    error.hidden = false;
  }
});
