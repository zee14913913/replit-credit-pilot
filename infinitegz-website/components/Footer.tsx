'use client'

import Link from 'next/link'

export default function Footer() {
  return (
    <footer id="contact" className="bg-infinitegz-black border-t border-infinitegz-gray">
      {/* Top CTA Section */}
      <div className="container mx-auto px-6 py-16 border-b border-infinitegz-gray">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          <div>
            <h3 className="text-3xl font-bold mb-2">Ready to optimize your finances?</h3>
            <p className="text-infinitegz-silver">Get started with CreditPilot today</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              href="https://portal.infinitegz.com"
              className="bg-infinitegz-white text-infinitegz-black px-8 py-3 rounded-full font-medium hover:bg-infinitegz-accent transition-all hover:scale-105 transform text-center"
            >
              Use CreditPilot on Web
            </Link>
            <Link
              href="https://wa.me/60123456789"
              className="bg-infinitegz-dark border border-infinitegz-gray text-infinitegz-white px-8 py-3 rounded-full font-medium hover:border-infinitegz-accent transition-all hover:scale-105 transform text-center"
            >
              Contact via WhatsApp
            </Link>
          </div>
        </div>
      </div>

      {/* Links Section */}
      <div className="container mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          {/* Company Info */}
          <div>
            <h3 className="text-2xl font-bold mb-6">INFINITE GZ</h3>
            <p className="text-sm text-infinitegz-silver leading-relaxed">
              Your trusted partner for loans, financial optimization, and digital transformation in Malaysia.
            </p>
          </div>

          {/* Products */}
          <div>
            <h4 className="font-bold mb-4 text-infinitegz-accent">PRODUCTS</h4>
            <ul className="space-y-3">
              <li>
                <Link href="/creditpilot" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  CreditPilot
                </Link>
              </li>
              <li>
                <Link href="/advisory" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Loan Advisory
                </Link>
              </li>
              <li>
                <Link href="/credit-card" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Credit Card Services
                </Link>
              </li>
              <li>
                <Link href="/accounting" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Accounting Services
                </Link>
              </li>
              <li>
                <Link href="/digital" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Digital Transformation
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-bold mb-4 text-infinitegz-accent">COMPANY</h4>
            <ul className="space-y-3">
              <li>
                <Link href="/about" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/careers" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Careers
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Contact
                </Link>
              </li>
              <li>
                <Link href="/news" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  News & Updates
                </Link>
              </li>
              <li>
                <Link href="/partners" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Partners
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="font-bold mb-4 text-infinitegz-accent">RESOURCES</h4>
            <ul className="space-y-3">
              <li>
                <Link href="/dsr-guide" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  DSR Guide
                </Link>
              </li>
              <li>
                <Link href="/tax-tips" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Tax Optimization Tips
                </Link>
              </li>
              <li>
                <Link href="/faq" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  FAQ
                </Link>
              </li>
              <li>
                <Link href="/blog" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Blog
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="container mx-auto px-6 py-6 border-t border-infinitegz-gray">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-infinitegz-silver">
            © 2024 INFINITE GZ SDN BHD. All rights reserved.
          </p>
          <div className="flex gap-6">
            <Link href="/terms" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
              Terms of Service
            </Link>
            <Link href="/privacy" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
              Privacy Policy
            </Link>
            <Link href="/legal" className="text-sm text-infinitegz-silver hover:text-infinitegz-white transition-colors">
              Legal
            </Link>
          </div>
        </div>
      </div>
    </footer>
  )
}
