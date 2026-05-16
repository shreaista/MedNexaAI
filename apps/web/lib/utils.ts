import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes without conflicting utilities — shadcn-style helper. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
