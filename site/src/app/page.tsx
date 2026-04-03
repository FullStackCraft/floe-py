"use client";

import Link from "next/link";
import { useState } from "react";

export default function Home() {
  const [copied, setCopied] = useState(false);
  const installCommand = "pip install floe-py";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(installCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <main className="min-h-screen overflow-y-auto flex flex-col items-center px-4 pt-14 md:pt-24 lg:pt-28 pb-8 md:pb-10">
      <div className="flex flex-col items-center w-full">
        <div className="text-center mb-20 md:mb-24">
          <h1 className="font-mono text-7xl md:text-8xl lg:text-9xl font-bold tracking-tight mb-6 text-[#0073b7]">
            floe
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Zero-dependency Python package for options flow: Black-Scholes pricing, Greeks, IV surfaces, dealer
            exposures, implied PDFs, hedge-flow analysis, and IV vs RV monitoring. Built for analytics pipelines,
            APIs, and production quant infrastructure.
          </p>
          <div className="mt-6">
            <a
              href="https://fullstackcraft.github.io/floe/whitepaper.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block font-bold text-white bg-[#0073b7] px-6 py-3 rounded hover:bg-[#005a8f] transition-colors"
            >
              Read Whitepaper
            </a>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-6 w-full max-w-4xl">
          <Link
            href="/documentation"
            className="flex-1 group border border-gray-200 rounded-lg p-8 hover:border-black transition-colors bg-white"
          >
            <h2 className="font-mono text-2xl font-semibold mb-3 group-hover:underline">Documentation</h2>
            <p className="text-gray-600">
              API reference, installation steps, and integration guidance for using floe in Python services.
            </p>
          </Link>

          <Link
            href="/examples"
            className="flex-1 group border border-gray-200 rounded-lg p-8 hover:border-black transition-colors bg-white"
          >
            <h2 className="font-mono text-2xl font-semibold mb-3 group-hover:underline">Examples</h2>
            <p className="text-gray-600">
              Practical Python examples for pricing, Greeks, IV analytics, dealer exposure mapping, and implied
              distributions.
            </p>
          </Link>

          <Link
            href="/playground"
            className="flex-1 group border border-gray-200 rounded-lg p-8 hover:border-black transition-colors bg-white"
          >
            <h2 className="font-mono text-2xl font-semibold mb-3 group-hover:underline">Playground</h2>
            <p className="text-gray-600">
              Browse ready-to-run Python snippets for common floe workflows and copy them directly into your codebase.
            </p>
          </Link>
        </div>

        <div className="mt-16 md:mt-20 mb-28 md:mb-40 lg:mb-48 text-center">
          <p className="text-sm text-gray-500 mb-3">{copied ? "Copied!" : "Quick install"}</p>
          <button
            onClick={handleCopy}
            className="font-mono text-sm bg-gray-100 px-4 py-2 rounded border border-gray-200 hover:border-gray-400 transition-colors cursor-pointer"
          >
            {installCommand}
          </button>
        </div>
      </div>

      <footer className="pt-2 pb-4 text-sm text-gray-400 flex flex-col items-center gap-2">
        <div>
          <a
            href="https://github.com/FullStackCraft/floe-py"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-black transition-colors"
          >
            GitHub
          </a>
          <span className="mx-3">·</span>
          <a
            href="https://pypi.org/project/floe-py/"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-black transition-colors"
          >
            PyPI
          </a>
          <span className="mx-3">·</span>
          <a
            href="https://fullstackcraft.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-black transition-colors"
          >
            Full Stack Craft
          </a>
        </div>
        <div className="text-xs mt-1">
          <a href="https://fullstackcraft.github.io/floe/" className="hover:text-black transition-colors">
            Looking for the TypeScript version?
          </a>
        </div>
        <div className="text-xs mt-1">
          <a href="https://fullstackcraft.github.io/floe-go/" className="hover:text-black transition-colors">
            Looking for the Go version?
          </a>
        </div>
        <div className="text-xs mt-1">© {new Date().getFullYear()} Full Stack Craft LLC</div>
      </footer>
    </main>
  );
}
