const style = (
  featureType: string | null,
  elementType: string | null,
  color?: string,
  visibility?: string,
  other?: Record<string, unknown>
): google.maps.MapTypeStyle => {
  const stylers: Record<string, unknown>[] = [];
  if (color) stylers.push({ color });
  if (visibility) stylers.push({ visibility });
  if (other) {
    Object.entries(other).forEach(([key, value]) => {
      stylers.push({ [key]: value });
    });
  }

  const item: google.maps.MapTypeStyle = { stylers };
  if (featureType) item.featureType = featureType;
  if (elementType) item.elementType = elementType;
  return item;
};

export const ghibliMapStyle = [
  style(null, 'geometry', '#FAF6EC'),
  style(null, 'labels.icon', undefined, 'simplified', { saturation: -20, gamma: 0.8 }),
  style(null, 'labels.text.fill', '#524A3D'),
  style(null, 'labels.text.stroke', '#ffffff', undefined, { weight: 3 }),
  style('administrative.land_parcel', 'labels.text.fill', '#bdbdbd'),
  style('poi', 'geometry', '#eeeeee'),
  style('poi', 'labels.text.fill', '#524A3D'),
  style('poi', 'labels.icon', undefined, 'on', { saturation: -20 }),
  style('poi.park', 'geometry', '#B3C4B0'),
  style('poi.park', 'labels.text.fill', '#3E4E3A'),
  style('road', 'geometry', '#ffffff'),
  style('road.arterial', 'labels.text.fill', '#757575'),
  style('road.highway', 'geometry', '#dadada'),
  style('road.highway', 'labels.text.fill', '#616161'),
  style('road.local', 'labels.text.fill', '#9e9e9e'),
  style('transit', 'labels.icon', undefined, 'on'),
  style('transit.line', 'geometry', '#e5e5e5'),
  style('transit.station', 'geometry', '#eeeeee'),
  style('water', 'geometry', '#C5E5F0'),
  style('water', 'labels.text.fill', '#5D8593'),
];
