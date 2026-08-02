export interface TreatPackage {
  amount: number;
  price: number;
  name: string;
  bonus: number;
  price_per_treat: number;
  // Computed property for UI logic (key from the object entries)
  key?: string;
}
