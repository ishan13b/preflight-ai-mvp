import { HomeExperience } from "@/components/home/home-experience";

export default function HomePage() {
  return (
    <main className="relative flex flex-1 flex-col">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,oklch(0.99_0.002_250),oklch(0.965_0.01_240))]"
      />
      <div className="relative z-10 flex flex-1 flex-col">
        <HomeExperience />
      </div>
    </main>
  );
}
