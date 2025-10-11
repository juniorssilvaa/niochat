import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

function Calendar({
  className,
  classNames,
  showOutsideDays = true,
  ...props
}) {
  // Implementação simples sem react-day-picker
  return (
    <div className={cn("p-3", className)}>
      <div className="text-center text-sm text-muted-foreground">
        Seletor de data simples
      </div>
      <div className="flex justify-center items-center gap-2 mt-4">
        <button className={cn(buttonVariants({ variant: "outline" }), "size-7")}>
          <ChevronLeft className="size-4" />
        </button>
        <span className="text-sm font-medium">Janeiro 2024</span>
        <button className={cn(buttonVariants({ variant: "outline" }), "size-7")}>
          <ChevronRight className="size-4" />
        </button>
      </div>
    </div>
  );
}

export { Calendar }
