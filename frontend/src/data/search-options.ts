export type CityOption = {
  name: string;
};

export type StateOption = {
  name: string;
  code: string;
  cities: CityOption[];
};

export type CountryOption = {
  name: string;
  iso2: string;
  iso3: string;
  states: StateOption[];
};

export const industryOptions = [
  "Restaurants",
  "Healthcare",
  "Clinics",
  "Real Estate",
  "Construction",
  "Retail",
  "Hospitality",
  "Education",
  "Logistics",
  "Manufacturing",
  "Financial Services",
  "Legal Services",
  "Marketing Agencies",
  "Automotive",
  "Beauty and Wellness"
];

export const countries: CountryOption[] = [
  {
    name: "Nigeria",
    iso2: "NG",
    iso3: "NGA",
    states: [
      {
        name: "Lagos",
        code: "LA",
        cities: [
          { name: "Ikeja" },
          { name: "Lekki" },
          { name: "Victoria Island" },
          { name: "Surulere" },
          { name: "Yaba" }
        ]
      },
      {
        name: "Abuja Federal Capital Territory",
        code: "FC",
        cities: [{ name: "Abuja" }, { name: "Gwarinpa" }, { name: "Maitama" }]
      },
      {
        name: "Rivers",
        code: "RI",
        cities: [{ name: "Port Harcourt" }, { name: "Bonny" }]
      }
    ]
  },
  {
    name: "United States",
    iso2: "US",
    iso3: "USA",
    states: [
      {
        name: "California",
        code: "CA",
        cities: [{ name: "Los Angeles" }, { name: "San Francisco" }, { name: "San Diego" }]
      },
      {
        name: "New York",
        code: "NY",
        cities: [{ name: "New York" }, { name: "Buffalo" }, { name: "Rochester" }]
      },
      {
        name: "Texas",
        code: "TX",
        cities: [{ name: "Houston" }, { name: "Austin" }, { name: "Dallas" }]
      }
    ]
  },
  {
    name: "United Kingdom",
    iso2: "GB",
    iso3: "GBR",
    states: [
      {
        name: "England",
        code: "ENG",
        cities: [{ name: "London" }, { name: "Manchester" }, { name: "Birmingham" }]
      },
      {
        name: "Scotland",
        code: "SCT",
        cities: [{ name: "Edinburgh" }, { name: "Glasgow" }]
      }
    ]
  },
  {
    name: "Canada",
    iso2: "CA",
    iso3: "CAN",
    states: [
      {
        name: "Ontario",
        code: "ON",
        cities: [{ name: "Toronto" }, { name: "Ottawa" }]
      },
      {
        name: "British Columbia",
        code: "BC",
        cities: [{ name: "Vancouver" }, { name: "Victoria" }]
      }
    ]
  },
  {
    name: "Ghana",
    iso2: "GH",
    iso3: "GHA",
    states: [
      {
        name: "Greater Accra",
        code: "AA",
        cities: [{ name: "Accra" }, { name: "Tema" }]
      },
      {
        name: "Ashanti",
        code: "AH",
        cities: [{ name: "Kumasi" }]
      }
    ]
  },
  {
    name: "Kenya",
    iso2: "KE",
    iso3: "KEN",
    states: [
      {
        name: "Nairobi",
        code: "30",
        cities: [{ name: "Nairobi" }, { name: "Westlands" }]
      },
      {
        name: "Mombasa",
        code: "28",
        cities: [{ name: "Mombasa" }]
      }
    ]
  },
  {
    name: "South Africa",
    iso2: "ZA",
    iso3: "ZAF",
    states: [
      {
        name: "Gauteng",
        code: "GP",
        cities: [{ name: "Johannesburg" }, { name: "Pretoria" }]
      },
      {
        name: "Western Cape",
        code: "WC",
        cities: [{ name: "Cape Town" }]
      }
    ]
  },
  {
    name: "United Arab Emirates",
    iso2: "AE",
    iso3: "ARE",
    states: [
      {
        name: "Dubai",
        code: "DU",
        cities: [{ name: "Dubai" }]
      },
      {
        name: "Abu Dhabi",
        code: "AZ",
        cities: [{ name: "Abu Dhabi" }]
      }
    ]
  },
  {
    name: "India",
    iso2: "IN",
    iso3: "IND",
    states: [
      {
        name: "Maharashtra",
        code: "MH",
        cities: [{ name: "Mumbai" }, { name: "Pune" }]
      },
      {
        name: "Karnataka",
        code: "KA",
        cities: [{ name: "Bengaluru" }]
      }
    ]
  }
];

export function getCountry(name: string) {
  return countries.find((country) => country.name === name);
}

export function getState(countryName: string, stateName: string) {
  return getCountry(countryName)?.states.find((state) => state.name === stateName);
}
