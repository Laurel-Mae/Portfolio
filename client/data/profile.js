// Public, approved portfolio content. Keep passwords, birthdate and private details out of this file.
// Text is rendered from this file; the HTML contains equivalent readable fallbacks for SEO/no-JS visitors.
export const profile = {
  identity: {
    name: 'Mae Ann Laurel',
    title: 'Networking & IT Support',
    status: 'IT Student', // Change to an accurate job title or graduate status when applicable.
    focus: 'Networking and IT support',
  },
  hero: {
    availability: 'OPEN TO INTERNSHIPS & CAREER OPPORTUNITIES',
    introduction: 'Interested in dependable networks, practical problem-solving, and making technology easier to use.',
    note: 'Learning through study, practice, and collaboration.',
    focus: 'Networks, systems, and the people who rely on them',
    direction: 'Internship & employment',
  },
  about: {
    headline: 'Reliable technology',
    headlineAccent: 'starts with people.',
    paragraphs: [
      'I am Mae Ann, an Information Technology student interested in computer networking and IT support. My focus is on how systems connect, how issues are investigated, and how clear technical assistance makes a difference.',
      'I am seeking opportunities to gain practical experience, contribute to a team, and develop the skills needed to support reliable day-to-day IT operations.',
    ],
  },
  portrait: {
    image: '/assets/images/mae-ann-1122.webp',
    alt: 'Portrait of Mae Ann Laurel',
    caption: 'The person behind the work.',
    subtitle: '', // Optional override. Empty = name + current identity.status.
  },
  contact: {
    email: '',
    whatsapp: '', // International format, e.g. +639XXXXXXXXX; no spaces required.
    phone: '',    // Optional public phone number; leave blank to hide.
  },
  documents: {
    // Place matching PDFs in client/assets/career/. No URLs are needed.
    resume: { title: 'Resume', filename: 'Mae-Ann-Laurel-Resume.pdf' },
    cv: { title: 'Curriculum Vitae', filename: 'Mae-Ann-Laurel-CV.pdf' },
  },
  credit: {
    name: 'Jhon Anthony Pano',
    url: 'https://jpano.dev',
  },
};
