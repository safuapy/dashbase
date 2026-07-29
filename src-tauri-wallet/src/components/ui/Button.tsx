import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/40 disabled:pointer-events-none disabled:opacity-40 cursor-pointer select-none active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--color-primary)] text-[#0a0e1a] font-semibold hover:bg-[var(--color-primary-hover)] glow-primary",
        secondary:
          "bg-[var(--color-surface-hover)] text-[var(--color-text)] hover:bg-[var(--color-surface-active)] border border-[var(--color-border)] hover:border-[var(--color-border-hover)]",
        danger:
          "bg-[var(--color-danger)] text-white hover:bg-red-600 shadow-lg shadow-red-500/20",
        ghost:
          "hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]",
        outline:
          "border border-[var(--color-border)] bg-transparent hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border-hover)] text-[var(--color-text)]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
