"use client";

import React, { forwardRef } from "react";
import { X } from "lucide-react";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onClear?: () => void;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className = "",
      type = "text",
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      onClear,
      value,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <div className="absolute left-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            type={type}
            value={value}
            disabled={disabled}
            className={`w-full h-10 text-sm bg-white dark:bg-slate-900 border text-slate-900 dark:text-slate-100 rounded-xl transition-all duration-150 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 disabled:bg-slate-50 dark:disabled:bg-slate-800 disabled:cursor-not-allowed ${
              leftIcon ? "pl-10" : "pl-3.5"
            } ${rightIcon || onClear ? "pr-10" : "pr-3.5"} ${
              error
                ? "border-rose-500 focus:border-rose-600 focus:ring-rose-500/20"
                : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
            } ${className}`}
            {...props}
          />
          {onClear && value && !disabled && (
            <button
              type="button"
              onClick={onClear}
              className="absolute right-3 p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-md transition-colors"
              aria-label="Clear input"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {rightIcon && !onClear && (
            <div className="absolute right-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <span className="text-xs text-rose-600 dark:text-rose-400 font-medium">
            {error}
          </span>
        ) : helperText ? (
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {helperText}
          </span>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
