import Nav from './components/Nav.jsx';
import Hero from './components/Hero.jsx';
import Problem from './components/Problem.jsx';
import Features from './components/Features.jsx';
import Demo from './components/Demo.jsx';
import Stack from './components/Stack.jsx';
import Datasets from './components/Datasets.jsx';
import Architecture from './components/Architecture.jsx';
import Footer from './components/Footer.jsx';

export default function App() {
  return (
    <>
      <Nav />
      <Hero />
      <Problem />
      <Features />
      <Demo />
      {/* <Stack /> */}
      <Datasets />
      <Architecture />
      <Footer />
    </>
  );
}
