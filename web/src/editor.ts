import { clamp, Component, contribution, density, initialComponents, lowerYear, maxComponents, maxSigma, minSigma, upperYear } from './prior';

const namespace = 'http://www.w3.org/2000/svg';
const left = 30;
const right = 970;
const baseline = 248;
const top = 48;
const colors = ['#698467', '#9b775e', '#71828e', '#91836b', '#897486', '#587e78'];
const yearX = (year: number) => left + (year - lowerYear) / (upperYear - lowerYear) * (right - left);
const xYear = (x: number) => lowerYear + (x - left) / (right - left) * (upperYear - lowerYear);

function node<K extends keyof SVGElementTagNameMap>(tag: K, attributes: Record<string, string | number>, text?: string): SVGElementTagNameMap[K] {
  const element = document.createElementNS(namespace, tag);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, String(value)));
  if (text) element.textContent = text;
  return element;
}

export class PriorEditor {
  components = initialComponents();
  selected = 0;
  private nextId = 4;
  private scale = 1;
  private drag: { id: number; role: string; x: number; y: number; initial: Component } | null = null;

  constructor(private readonly svg: SVGSVGElement) {
    svg.addEventListener('pointerdown', event => this.start(event));
    svg.addEventListener('pointermove', event => this.move(event));
    svg.addEventListener('pointerup', () => this.finish());
    svg.addEventListener('pointercancel', () => this.finish());
    svg.addEventListener('keydown', event => this.key(event));
    svg.addEventListener('contextmenu', event => {
      const handle = (event.target as Element).closest('[data-id]');
      if (handle) { event.preventDefault(); this.remove(Number(handle.getAttribute('data-id'))); }
    });
    this.render();
  }

  private coordinates(event: PointerEvent) {
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(this.svg.getScreenCTM()!.inverse());
    return { x: point.x, y: point.y };
  }

  private start(event: PointerEvent) {
    if (event.button !== 0) return;
    const { x, y } = this.coordinates(event);
    const handle = (event.target as Element).closest('[data-id]');
    if (!handle) {
      if (x < left || x > right || y < top || y > baseline || this.components.length >= maxComponents) return;
      const component = { id: this.nextId++, mean: clamp(xYear(x), lowerYear, upperYear), sigma: 2, weight: 1 };
      this.components.push(component);
      this.selected = component.id;
      this.render();
      return;
    }
    const id = Number(handle.getAttribute('data-id'));
    const role = handle.getAttribute('data-role') ?? 'center';
    if (role === 'remove') { this.remove(id); return; }
    const component = this.components.find(item => item.id === id)!;
    this.selected = id;
    this.drag = { id, role, x, y, initial: { ...component } };
    this.svg.setPointerCapture(event.pointerId);
    this.render();
    event.preventDefault();
  }

  private move(event: PointerEvent) {
    if (!this.drag) return;
    const point = this.coordinates(event);
    const component = this.components.find(item => item.id === this.drag!.id)!;
    if (this.drag.role === 'center') {
      component.mean = clamp(this.drag.initial.mean + (point.x - this.drag.x) * 60 / (right - left), lowerYear, upperYear);
    } else if (this.drag.role === 'width') {
      component.sigma = clamp(Math.abs(xYear(point.x) - component.mean), minSigma, maxSigma);
    } else if (this.drag.role === 'weight') {
      component.weight = clamp(this.drag.initial.weight * Math.exp((this.drag.y - point.y) / 65), 0.02, 1000);
    }
    this.render(false);
  }

  private finish() { this.drag = null; this.render(); }

  private remove(id: number) {
    if (this.components.length === 1) return;
    this.components = this.components.filter(component => component.id !== id);
    if (this.selected === id) this.selected = this.components[0].id;
    this.render();
  }

  private key(event: KeyboardEvent) {
    const handle = (event.target as Element).closest('[data-id]');
    if (!handle) return;
    const id = Number(handle.getAttribute('data-id'));
    const component = this.components.find(item => item.id === id)!;
    this.selected = id;
    if (event.key === 'Delete' || event.key === 'Backspace' || ((event.key === 'Enter' || event.key === ' ') && handle.getAttribute('data-role') === 'remove')) {
      event.preventDefault(); this.remove(id); return;
    }
    if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'ArrowUp' || event.key === 'ArrowDown') component.weight = clamp(component.weight * (event.key === 'ArrowUp' ? 1.1 : 1 / 1.1), 0.02, 1000);
    else if (event.shiftKey) component.sigma = clamp(component.sigma + (event.key === 'ArrowRight' ? 0.25 : -0.25), minSigma, maxSigma);
    else component.mean = clamp(component.mean + (event.key === 'ArrowRight' ? 0.5 : -0.5), lowerYear, upperYear);
    const role = handle.getAttribute('data-role');
    this.render();
    (this.svg.querySelector(`[data-id="${id}"][data-role="${role}"]`) as SVGElement | null)?.focus();
  }

  render(rescale = true) {
    const focus = document.activeElement as Element | null;
    const focusId = focus?.getAttribute('data-id');
    const focusRole = focus?.getAttribute('data-role');
    const samples = Array.from({ length: 601 }, (_, index) => lowerYear + index / 10);
    const composite = samples.map(year => density(this.components, year));
    if (rescale) this.scale = (baseline - top - 20) / Math.max(0.025, ...composite);
    const y = (value: number) => baseline - value * this.scale;
    const total = this.components.reduce((sum, component) => sum + component.weight, 0);
    this.svg.replaceChildren();
    const background = node('g', { 'pointer-events': 'none' });
    [0, 1, 2, 3].forEach(index => background.append(node('line', { x1: left, x2: right, y1: top + index * (baseline - top) / 3, y2: top + index * (baseline - top) / 3, class: 'plot-grid' })));
    for (let year = lowerYear; year <= upperYear; year += 10) {
      background.append(node('line', { x1: yearX(year), x2: yearX(year), y1: top, y2: baseline, class: 'plot-grid' }));
      background.append(node('text', { x: yearX(year), y: 279, 'text-anchor': 'middle', class: 'year-label' }, String(year)));
    }
    background.append(node('text', { x: left, y: 23, class: 'plot-label' }, 'PROBABILITY DENSITY'));
    background.append(node('text', { x: right, y: 302, 'text-anchor': 'end', class: 'plot-label' }, 'YEAR'));
    this.svg.append(background);
    this.components.forEach(component => {
      const color = colors[component.id % colors.length];
      const points = samples.map(year => `${yearX(year)},${y(contribution(component, year, total))}`).join(' L ');
      this.svg.append(node('path', { d: `M ${left},${baseline} L ${points} L ${right},${baseline} Z`, fill: color, 'fill-opacity': 0.08, stroke: color, 'stroke-opacity': 0.38, 'stroke-width': 1.5, 'stroke-dasharray': '4 5', 'pointer-events': 'none' }));
    });
    const compositePath = `M ${samples.map((year, index) => `${yearX(year)},${y(composite[index])}`).join(' L ')}`;
    this.svg.append(node('path', { id: 'composite-fill', d: `${compositePath} L ${right},${baseline} L ${left},${baseline} Z`, fill: '#526e50', 'fill-opacity': 0.13, 'pointer-events': 'none' }));
    this.svg.append(node('path', { id: 'composite-curve', d: compositePath, stroke: '#365c3c', 'stroke-width': 2.5, fill: 'none', 'pointer-events': 'none' }));
    this.components.forEach(component => {
      const color = colors[component.id % colors.length];
      const x = yearX(component.mean);
      const apex = clamp(y(contribution(component, component.mean, total)), top, baseline - 8);
      const chosen = component.id === this.selected;
      const handleAttributes = { 'data-id': component.id, tabindex: '0', role: 'button', 'aria-pressed': String(chosen) };
      this.svg.append(node('line', { x1: x, x2: x, y1: apex, y2: baseline, stroke: color, 'stroke-width': chosen ? 1.5 : 1, 'stroke-opacity': 0.6, 'pointer-events': 'none' }));
      this.svg.append(node('circle', { ...handleAttributes, cx: x, cy: apex, r: chosen ? 7 : 5, fill: color, stroke: '#f5f3eb', 'stroke-width': 2, 'data-role': 'weight', 'aria-label': `Component ${component.id + 1}, adjust relative weight`, class: 'weight-handle' }));
      this.svg.append(node('circle', { ...handleAttributes, cx: x, cy: baseline, r: 7, fill: chosen ? color : '#f5f3eb', stroke: color, 'stroke-width': 2, 'data-role': 'center', 'aria-label': `Component ${component.id + 1}, temporal center ${component.mean.toFixed(1)}`, class: 'center-handle' }));
      if (chosen) {
        const widthX = yearX(component.mean + (component.mean > 2022 ? -1 : 1) * component.sigma);
        this.svg.append(node('line', { x1: x, x2: widthX, y1: baseline - 22, y2: baseline - 22, stroke: color, 'pointer-events': 'none' }));
        this.svg.append(node('rect', { ...handleAttributes, x: widthX - 5, y: baseline - 29, width: 10, height: 14, rx: 2, fill: color, 'data-role': 'width', 'aria-label': `Component ${component.id + 1}, width ${component.sigma.toFixed(1)} years`, class: 'width-handle' }));
        const labelX = right - 145;
        this.svg.append(node('text', { x: labelX, y: 23, 'text-anchor': 'middle', class: 'component-label', 'pointer-events': 'none' }, `${component.mean.toFixed(1)}  ·  σ ${component.sigma.toFixed(1)}  ·  w ${component.weight.toFixed(2)}`));
        if (this.components.length > 1) {
          const removal = node('g', { ...handleAttributes, 'data-role': 'remove', 'aria-label': `Remove component ${component.id + 1}`, class: 'remove-handle' });
          removal.append(node('rect', { x: labelX + 108, y: 8, width: 22, height: 22, rx: 11, fill: '#e8e7dd' }));
          removal.append(node('text', { x: labelX + 119, y: 24, 'text-anchor': 'middle', fill: '#586055', 'pointer-events': 'none' }, '×'));
          this.svg.append(removal);
        }
      }
    });
    this.svg.dataset.components = JSON.stringify(this.components);
    this.svg.dataset.scale = String(this.scale);
    document.querySelector('#prior-status')!.textContent = `${this.components.length} components. Unit probability mass.`;
    if (focusId && focusRole) (this.svg.querySelector(`[data-id="${focusId}"][data-role="${focusRole}"]`) as SVGElement | null)?.focus();
  }

  payload() { return { components: this.components.map(({ mean, sigma, weight }) => ({ mean, sigma, weight })) }; }
}
