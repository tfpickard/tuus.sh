export interface Component { id: number; mean: number; sigma: number; weight: number }
export const lowerYear = 1970;
export const upperYear = 2030;
export const maxComponents = 6;
export const minSigma = 0.5;
export const maxSigma = 8;
export const clamp = (value: number, minimum: number, maximum: number) => Math.min(maximum, Math.max(minimum, value));

// Abramowitz–Stegun 7.1.26. Absolute CDF error is below 1.5e-7.
export function normalCdf(value: number): number {
  const sign = value < 0 ? -1 : 1;
  const x = Math.abs(value) / Math.sqrt(2);
  const t = 1 / (1 + 0.3275911 * x);
  const polynomial = (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t;
  const erf = sign * (1 - polynomial * Math.exp(-x * x));
  return 0.5 * (1 + erf);
}

export function contribution(component: Component, year: number, totalWeight: number): number {
  if (year < lowerYear || year > upperYear) return 0;
  const mass = normalCdf((upperYear - component.mean) / component.sigma) - normalCdf((lowerYear - component.mean) / component.sigma);
  const z = (year - component.mean) / component.sigma;
  return (component.weight / totalWeight) * Math.exp(-0.5 * z * z) / (component.sigma * Math.sqrt(2 * Math.PI) * mass);
}

export function density(components: Component[], year: number): number {
  const total = components.reduce((sum, component) => sum + component.weight, 0);
  return components.reduce((sum, component) => sum + contribution(component, year, total), 0);
}

export function initialComponents(): Component[] {
  return [1976, 1992, 2008, 2024].map((mean, id) => ({ id, mean, sigma: 8, weight: 1 }));
}
