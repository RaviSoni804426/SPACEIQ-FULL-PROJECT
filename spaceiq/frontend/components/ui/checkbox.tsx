import { cn } from "@/lib/utils";

export function Checkbox({
  checked,
  onChange,
  className,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={cn(
        "flex h-4 w-4 items-center justify-center rounded border border-border transition-colors",
        checked ? "bg-primary border-primary text-white" : "bg-white",
        className,
      )}
    >
      {checked ? <span className="text-[10px]">✓</span> : null}
    </button>
  );
}
