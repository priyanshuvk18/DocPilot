import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const spring = {
  soft: { type: "spring", stiffness: 170, damping: 22 },
  snappy: { type: "spring", stiffness: 380, damping: 30 },
  float: { type: "spring", stiffness: 60, damping: 14, mass: 1.2 },
};
