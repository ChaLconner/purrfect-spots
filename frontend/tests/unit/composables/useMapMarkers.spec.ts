import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import { useMapMarkers } from '@/composables/useMapMarkers';
import { EXTERNAL_URLS } from '@/utils/constants';

const clustererMocks = vi.hoisted(() => ({
  addMarkers: vi.fn(),
  removeMarkers: vi.fn(),
  clearMarkers: vi.fn(),
  render: vi.fn(),
}));

vi.mock('@googlemaps/markerclusterer', () => ({
  MarkerClusterer: class {
    addMarkers = clustererMocks.addMarkers;
    removeMarkers = clustererMocks.removeMarkers;
    clearMarkers = clustererMocks.clearMarkers;
    render = clustererMocks.render;
  },
  SuperClusterAlgorithm: class {},
}));

class MockMarker {
  static MAX_ZINDEX = 1_000_000;
  static instances: MockMarker[] = [];

  readonly options: Record<string, unknown>;
  readonly setIcon = vi.fn((icon: unknown) => {
    this.options.icon = icon;
  });
  readonly setPosition = vi.fn();
  readonly setTitle = vi.fn();
  readonly setMap = vi.fn();
  readonly addListener = vi.fn().mockReturnValue({ remove: vi.fn() });

  constructor(options: Record<string, unknown>) {
    this.options = { ...options };
    MockMarker.instances.push(this);
  }

  getPosition(): { lat: () => number; lng: () => number } | null {
    const position = this.options.position as { lat: number; lng: number } | undefined;
    return position
      ? { lat: () => position.lat, lng: () => position.lng }
      : null;
  }
}

class MockCircle {
  static instances: MockCircle[] = [];

  readonly setMap = vi.fn();
  readonly setOptions = vi.fn((options: Record<string, unknown>) => {
    this.options = { ...this.options, ...options };
  });
  options: Record<string, unknown>;

  constructor(options: Record<string, unknown>) {
    this.options = { ...options };
    MockCircle.instances.push(this);
  }
}

class MockSize {
  constructor(
    readonly width: number,
    readonly height: number
  ) {}
}

class MockPoint {
  constructor(
    readonly x: number,
    readonly y: number
  ) {}
}

class MockImage {
  static instances: MockImage[] = [];

  crossOrigin = '';
  decoding = '';
  width = 52;
  height = 52;
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  private imageSource = '';

  constructor() {
    MockImage.instances.push(this);
  }

  set src(value: string) {
    this.imageSource = value;
  }

  get src(): string {
    return this.imageSource;
  }
}

const fillStyles: string[] = [];
const canvasContext = {
  shadowColor: '',
  shadowBlur: 0,
  shadowOffsetY: 0,
  strokeStyle: '',
  lineWidth: 0,
  globalAlpha: 1,
  save: vi.fn(),
  restore: vi.fn(),
  beginPath: vi.fn(),
  closePath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  bezierCurveTo: vi.fn(),
  arc: vi.fn(),
  clip: vi.fn(),
  stroke: vi.fn(),
  drawImage: vi.fn(),
  fill: vi.fn(),
  set fillStyle(value: string) {
    fillStyles.push(value);
  },
};

const map = {
  addListener: vi.fn(),
};

describe('useMapMarkers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    MockImage.instances = [];
    MockMarker.instances = [];
    MockCircle.instances = [];
    fillStyles.length = 0;

    vi.stubGlobal('Image', MockImage);
    vi.stubGlobal('google', {
      maps: {
        Marker: MockMarker,
        Size: MockSize,
        Point: MockPoint,
        Circle: MockCircle,
        SymbolPath: { CIRCLE: 0 },
        marker: {},
        event: { removeListener: vi.fn() },
      },
    });

    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
      canvasContext as unknown as CanvasRenderingContext2D
    );
    vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockReturnValue(
      'data:image/png;base64,themed-cat-marker'
    );
  });

  it('renders cat image inside a theme-colored marker', () => {
    const { updateMarkers, markers } = useMapMarkers(ref(map as google.maps.Map));
    const location = {
      id: 'cat-1',
      latitude: 13.7563,
      longitude: 100.5018,
      location_name: 'Bangkok',
      image_url: 'https://cdn.example.test/cat-1.jpg',
    };

    updateMarkers([location]);

    const marker = markers.value.get(location.id) as unknown as MockMarker;
    expect(marker.options.icon).toEqual(
      expect.objectContaining({ url: EXTERNAL_URLS.CAT_MARKER_ICON })
    );
    expect(MockImage.instances).toHaveLength(1);
    expect(MockImage.instances[0].crossOrigin).toBe('anonymous');
    expect(MockImage.instances[0].src).toBe(location.image_url);

    MockImage.instances[0].onload?.();

    expect(marker.setIcon).toHaveBeenCalledWith(
      expect.objectContaining({
        url: 'data:image/png;base64,themed-cat-marker',
        scaledSize: expect.objectContaining({ width: 52, height: 72 }),
      })
    );
    expect(fillStyles).toContain('#d67a4f');
    expect(fillStyles).toContain('#faf6ec');
  });

  it('keeps the themed fallback marker when no image exists', () => {
    const { updateMarkers, markers } = useMapMarkers(ref(map as google.maps.Map));

    updateMarkers([
      {
        id: 'cat-without-image',
        latitude: 13.7563,
        longitude: 100.5018,
        location_name: 'Bangkok',
        image_url: '',
      },
    ]);

    const marker = markers.value.get('cat-without-image') as unknown as MockMarker;
    expect(marker.options.icon).toEqual(
      expect.objectContaining({ url: EXTERNAL_URLS.CAT_MARKER_ICON })
    );
    expect(MockImage.instances).toHaveLength(0);
  });

  it('updates the user marker, accuracy circle, and radius circle', () => {
    const { updateUserMarker, updateUserRadiusCircle } = useMapMarkers(ref(map as google.maps.Map));
    const position = { lat: 13.7563, lng: 100.5018 };

    updateUserMarker(position, { accuracy: 25, title: 'Current location' });
    const marker = MockMarker.instances.at(-1);
    expect(marker?.options.title).toBe('Current location');
    expect(MockCircle.instances.at(-1)?.options.radius).toBe(25);

    updateUserMarker(position, { accuracy: 10, stale: true, title: 'Stale location' });
    expect(marker?.setPosition).toHaveBeenCalledWith(position);
    expect(marker?.setTitle).toHaveBeenCalledWith('Stale location');
    expect(MockCircle.instances.at(-1)?.setOptions).toHaveBeenCalled();

    updateUserRadiusCircle(2, position);
    const radiusCircle = MockCircle.instances.at(-1);
    expect(radiusCircle?.options.radius).toBe(2000);
    updateUserRadiusCircle(3, position);
    expect(radiusCircle?.setOptions).toHaveBeenCalled();
    updateUserRadiusCircle(null, null);
    expect(radiusCircle?.setMap).toHaveBeenCalledWith(null);

    updateUserMarker(null);
    expect(marker?.setMap).toHaveBeenCalledWith(null);
  });
});
